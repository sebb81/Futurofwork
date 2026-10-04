import hashlib
import json
import re
import unicodedata
import uuid
from .store import DomainError, Store


def normalize(text):
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")


def fingerprint(s):
    keys = ["context", "constraints", "resources", "assignments", "space_id", "annotations", "perturbation", "recipe"]
    return hashlib.sha256(json.dumps({k: s[k] for k in keys}, sort_keys=True).encode()).hexdigest()


def find(items, ident):
    item = next((i for i in items if i["id"] == ident), None)
    if not item:
        raise DomainError(f"Objet inconnu : {ident}")
    return item


def effective_constraints(s):
    c = dict(s["constraints"])
    if "m-access" in s["context"]:
        c["aisle_cm"] = max(c["aisle_cm"], 140)
        c["quiet_places"] = max(c["quiet_places"], 12)
    return c


def check_assignment(s, rid, zone, start, end):
    r = find(s["resources"], rid)
    space = find(s["spaces"], s["space_id"])
    z = find(space["zones"], zone)
    if not r["available"]:
        raise DomainError(f"{r['name']} est indisponible")
    if zone not in r["allowed_zones"] or z["capacity"] <= 0:
        raise DomainError(f"{r['name']} ne convient pas à cette zone")
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", start) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", end) or start >= end:
        raise DomainError("Créneau invalide")
    if start < "08:00" or end > "12:00":
        raise DomainError("Le matériel doit être disponible entre 08:00 et 12:00")
    return {"resource_id": rid, "zone": zone, "start": start, "end": end}


def estimate(s, space_id, resource_ids):
    space = find(s["spaces"], space_id)
    if len(set(resource_ids)) != len(resource_ids):
        raise DomainError("Matériel compté deux fois")
    resources = [find(s["resources"], i) for i in resource_ids]
    lines = [{"name": space["name"], "amount": space["cost"]}]
    lines += [{"name": r["name"], "amount": r["cost"]} for r in resources]
    lines += [{"name": "Accueil et accessibilité", "amount": 600}, {"name": "Réserve imprévus", "amount": 400}]
    return {"lines": lines, "total": sum(l["amount"] for l in lines), "limit": effective_constraints(s)["budget"]}


def critique(s, plan):
    c = effective_constraints(s)
    space = find(s["spaces"], plan["space_id"])
    warnings = []
    if not space["accessible"]:
        warnings.append("Le lieu comporte des marches")
    if space["capacity"] < c["visitors"]:
        warnings.append("Capacité totale insuffisante")
    if space["aisle_cm"] < c["aisle_cm"]:
        warnings.append("Cheminement trop étroit")
    if space["quiet_capacity"] < c["quiet_places"]:
        warnings.append("Zone calme insuffisante")
    counts = plan.get("occupancy", {})
    if sum(counts.values()) != c["visitors"] or set(counts) != {z["id"] for z in space["zones"]}:
        warnings.append("La répartition doit couvrir tous les visiteurs et les zones")
    for z in space["zones"]:
        if counts.get(z["id"], 0) > z["capacity"] or counts.get(z["id"], 0) < 0:
            warnings.append(f"Capacité dépassée : {z['name']}")
    if counts.get("calme", 0) < c["quiet_places"]:
        warnings.append("Pas assez de places calmes réservées")
    if "m-access" not in s["context"]:
        warnings.append("La décision d'accessibilité n'est pas dans le contexte actif : ajoutez-la pour la prendre en compte")
    if estimate(s, plan["space_id"], plan["resource_ids"])["total"] > c["budget"]:
        warnings.append("Budget dépassé")
    for rid in plan["resource_ids"]:
        if not find(s["resources"], rid)["available"]:
            warnings.append(f"Matériel indisponible : {rid}")
    focus = plan.get("focus", {})
    for rid in focus.get("resource_ids", []):
        if rid not in plan["resource_ids"] or focus.get("zone") not in find(s["resources"], rid)["allowed_zones"]:
            warnings.append("Sélection visuelle incompatible")
    required = {"audio", "table-a", "table-b", "quiet", "signs"}
    if not required.issubset(plan["resource_ids"]) or not {"led", "screen"}.intersection(plan["resource_ids"]):
        warnings.append("Le plan ne couvre pas les équipements essentiels")
    return warnings


class Services:
    """Eight bounded services. Only synthetic session data is accessible."""
    def __init__(self, store: Store):
        self.store = store

    def call(self, service, sid, args):
        method = getattr(self, service.lower(), None)
        if not method or service not in ["Memory", "Resources", "Space", "Calendar", "Budget", "Documents", "Messaging", "Workspace"]:
            raise DomainError("Outil inconnu")
        result = method(sid, args)
        self.store.event(sid, "tool.result", {"tool": service, "operation": args.get("operation", "read"), "result": result})
        return result

    def memory(self, sid, a):
        s = self.store.get(sid)["state"]
        query = normalize(a.get("query", ""))
        words = [w for w in re.findall(r"[a-z0-9]+", query) if len(w) > 3]
        scored = []
        for m in s["memory"]:
            hay = normalize(m["title"] + " " + m["text"] + " " + " ".join(m["tags"]))
            score = sum(w in hay for w in words)
            if score or not words:
                scored.append({**m, "score": score, "evidence": "retrouvée", "in_context": m["id"] in s["context"]})
        scored.sort(key=lambda m: (not bool(m["superseded_by"]), m["score"], m["date"]), reverse=True)
        return {"items": scored, "active_context": s["context"], "method": "Recherche lexicale locale, sans déduction générative"}

    def resources(self, sid, a):
        s = self.store.get(sid)["state"]
        return {"items": s["resources"], "assignments": s["assignments"]}

    def space(self, sid, a):
        return {"items": self.store.get(sid)["state"]["spaces"]}

    def calendar(self, sid, a):
        if a.get("operation") != "schedule":
            return {"availability": self.store.get(sid)["state"]["calendar"]}
        def schedule(s):
            self.approved(s, a)
            s["schedule"] = s["calendar"] + [{"id": "setup", "name": "Installation · équipe HORIZON", "start": "08:00", "end": "09:00", "zone": "scene"}]
            return {"schedule": s["schedule"]}
        return self.store.mutate(sid, "calendar.scheduled", schedule, snapshot=False)

    def budget(self, sid, a):
        s = self.store.get(sid)["state"]
        return estimate(s, a["space_id"], a["resource_ids"])

    def documents(self, sid, a):
        def generate(s):
            p = self.approved(s, a)
            space = find(s["spaces"], p["plan"]["space_id"])
            doc = {"id": str(uuid.uuid4()), "title": "Plan d'ouverture HORIZON", "kind": "markdown", "content":
                f"# HORIZON · {space['name']}\n\n{effective_constraints(s)['visitors']} visiteurs · ouverture dans 48 heures.\n\n"
                f"Budget : {p['budget']['total']} € / {p['budget']['limit']} €.\n\n"
                f"Cheminement : {space['aisle_cm']} cm. Zone calme : {space['quiet_capacity']} places.\n\n"
                + "\n".join(f"- {find(s['resources'], rid)['name']} → {v['zone']} ({v['start']}–{v['end']})" for rid, v in s["assignments"].items())
                + "\n\n## Sources actives\n" + "\n".join(f"- {find(s['memory'], mid)['source']}" for mid in s["context"])
                + "\n\n## Planning\n" + "\n".join(f"- {e['start']}–{e['end']} : {e['name']}" for e in s["schedule"])}
            s["documents"].append(doc)
            return doc
        return self.store.mutate(sid, "documents.created", generate, snapshot=False)

    def messaging(self, sid, a):
        def draft(s):
            p = self.approved(s, a)
            space = find(s["spaces"], p["plan"]["space_id"])
            msg = {"id": str(uuid.uuid4()), "title": "Nouvelle implantation · équipe & visiteurs", "status": "draft",
                   "content": f"L'événement HORIZON vous accueille au {space['name']} à 09:00. Accès sans marches, cheminement de {space['aisle_cm']} cm et zone calme de {space['quiet_capacity']} places. L'installation commence à 08:00. Ce message est un brouillon fictif, aucun envoi externe."}
            s["messages"].append(msg)
            return msg
        return self.store.mutate(sid, "messaging.drafted", draft, snapshot=False)

    def approved(self, s, a):
        p = s["proposal"]
        if not p or p["id"] != a.get("proposal_id") or p["status"] != "executing":
            raise DomainError("Validation humaine requise")
        return p

    def workspace(self, sid, a):
        op = a.get("operation", "read")
        if op == "read":
            s = self.store.get(sid)["state"]
            return {"context": s["context"], "constraints": effective_constraints(s), "assignments": s["assignments"], "recipe": s["recipe"]}
        if op == "preview":
            def preview(s):
                plan = a["plan"]
                warnings = critique(s, plan)
                p = {"id": str(uuid.uuid4()), "status": "pending", "plan": plan, "budget": estimate(s, plan["space_id"], plan["resource_ids"]),
                     "warnings": warnings, "fingerprint": fingerprint(s), "reason": a.get("reason", "Choix du scénario prédéfini"), "source": a.get("source", "demo")}
                s["proposal"] = p
                return p
            return self.store.mutate(sid, "decision.proposed", preview, snapshot=False)
        if op == "apply":
            def apply(s):
                p = self.approved(s, a)
                if fingerprint(s) != p["fingerprint"] or critique(s, p["plan"]):
                    raise DomainError("Proposition obsolète ou invalide ; relancez la préparation")
                s["space_id"] = p["plan"]["space_id"]
                s["assignments"] = {}
                for rid in p["plan"]["resource_ids"]:
                    zone = {"display": "scene", "audio": "scene", "table": "atelier", "quiet": "calme", "signs": "scene"}[find(s["resources"], rid)["kind"]]
                    focus = p["plan"].get("focus", {})
                    if rid in focus.get("resource_ids", []):
                        zone = focus["zone"]
                    # Reuse the demonstrated parameters for compatible resources, if a recipe exists.
                    recipe = s["recipe"]
                    if recipe and zone == recipe["zone"]:
                        start, end = recipe["start"], recipe["end"]
                    else:
                        start, end = "09:00", "12:00"
                    s["assignments"][rid] = check_assignment(s, rid, zone, start, end)
                s["budget"] = p["budget"]
                return {"space_id": s["space_id"], "assignments": s["assignments"], "budget": s["budget"], "recipe_used": bool(s["recipe"])}
            return self.store.mutate(sid, "workspace.applied", apply, snapshot=False)
        if op == "complete":
            def complete(s):
                p = self.approved(s, a)
                p["status"] = "completed"
                return {"proposal_id": p["id"], "status": "completed"}
            return self.store.mutate(sid, "mission.completed", complete, snapshot=False)
        raise DomainError("Opération workspace inconnue")

    def interact(self, sid, action, data):
        def apply(s):
            if action == "context":
                mid = data["id"]
                m = find(s["memory"], mid)
                if data.get("enabled", True):
                    if m["superseded_by"]:
                        raise DomainError("Cette source est obsolète : utilisez sa version actualisée")
                    if mid not in s["context"]:
                        s["context"].append(mid)
                elif mid in s["context"]:
                    s["context"].remove(mid)
                return {"context": s["context"], "effective_constraints": effective_constraints(s)}
            if action == "assign":
                assignment = check_assignment(s, data["id"], data["zone"], data.get("start", "09:00"), data.get("end", "12:00"))
                s["assignments"][data["id"]] = assignment
                if s["recording"]:
                    s["recorded"].append({"type": "assign", "object_type": "resource", **assignment})
                return assignment
            if action == "record_start":
                s["recording"], s["recorded"], s["recipe"] = True, [], None
                return {"recording": True}
            if action == "record_finish":
                if not s["recording"] or not s["recorded"]:
                    raise DomainError("Enregistrez au moins une affectation avant de terminer")
                ids = {e["resource_id"] for e in s["recorded"]}
                if len(ids) != 1:
                    raise DomainError("Démontrez sur une seule ressource : l'identifiant devient le paramètre variable")
                last = s["recorded"][-1]
                s["recipe"] = {"variable": "resource_id", "zone": last["zone"], "start": last["start"], "end": last["end"], "steps": list(s["recorded"])}
                s["recording"] = False
                return s["recipe"]
            if action == "replay":
                if not s["recipe"] or not data.get("ids"):
                    raise DomainError("Recette et sélection de ressources nécessaires")
                recipe = s["recipe"]
                result = []
                # Transaction validates every step and rolls back the whole batch on any error.
                for rid in data["ids"]:
                    for step in recipe["steps"]:
                        assignment = check_assignment(s, rid, step["zone"], step["start"], step["end"])
                        s["assignments"][rid] = assignment
                        result.append(assignment)
                s["last_replay"] = {"count": len(data["ids"]), "actions": result}
                return s["last_replay"]
            if action == "annotate":
                points = data.get("points", [])
                if not 2 <= len(points) <= 500 or any(not isinstance(p, list) or len(p) != 2 or any(not isinstance(v, (int, float)) or not 0 <= v <= 100 for v in p) for p in points):
                    raise DomainError("Annotation invalide")
                s["annotations"].append({"id": str(uuid.uuid4()), "points": points, "label": str(data.get("label", "Zone sélectionnée"))[:100]})
                return {"annotations": len(s["annotations"])}
            if action == "constraint":
                key, value = data.get("key"), data.get("value")
                bounds = {"budget": (1000, 20000), "visitors": (10, 200), "aisle_cm": (90, 200), "quiet_places": (0, 30)}
                if key not in bounds or not isinstance(value, int) or not bounds[key][0] <= value <= bounds[key][1]:
                    raise DomainError("Contrainte invalide")
                s["constraints"][key] = value
                return {"constraints": effective_constraints(s)}
            if action == "card":
                code = str(data.get("code", "")).upper().strip()
                if code == "ACCES140":
                    if "m-access" not in s["context"]:
                        s["context"].append("m-access")
                elif code == "CALME12":
                    s["constraints"]["quiet_places"] = 12
                elif code == "BUDGET5500":
                    s["constraints"]["budget"] = 5500
                else:
                    raise DomainError("Code inconnu : ACCES140, CALME12 ou BUDGET5500")
                return {"card": code, "constraints": effective_constraints(s)}
            if action == "roles":
                s["roles"] = (s["roles"] + 1) % 3
                return {"rotation": s["roles"]}
            if action == "phase":
                phase = data.get("phase")
                if not isinstance(phase, int) or phase not in range(5):
                    raise DomainError("Séquence invalide")
                s["phase"] = phase
                return {"phase": phase}
            raise DomainError("Action inconnue")
        return self.store.mutate(sid, f"human.{action}", apply)
