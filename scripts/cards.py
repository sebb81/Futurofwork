"""Generate real, offline QR cards for the workshop host URL."""
import argparse
import html
from pathlib import Path
import segno

parser = argparse.ArgumentParser()
parser.add_argument("--base-url", default="http://localhost:8000")
args = parser.parse_args()
base = args.base_url.rstrip("/")
cards = [("ACCES140", "Un espace pour tout le monde.", "Cheminement libre de 140 cm, sans marches, et 12 places calmes. Ajoute la décision sourcée au contexte."),
         ("CALME12", "Du calme, au milieu des possibles.", "Réserve au moins 12 places dans une zone calme."),
         ("BUDGET5500", "Faire mieux avec moins.", "La nouvelle enveloppe maximale est de 5 500 €. Le choix de lieu devra s'adapter.")]
items = []
for group in range(1, 6):
    for code, title, description in cards:
        qr = segno.make(base + "/?card=" + code, micro=False)
        items.append(f'<article><header>WORK/2030 <span>TRINÔME 0{group}</span></header><h2>{title}</h2><p>{description}</p><img src="{qr.svg_data_uri(scale=3, border=4)}" alt="QR de la carte {code}"/><strong>{code}</strong><small>Scannez, choisissez votre groupe, puis ajoutez la carte. Sans caméra : saisissez le code dans votre espace.</small></article>')
page = '''<!doctype html><html lang="fr"><meta charset="utf-8"><title>WORK/2030 — Cartes d'intention</title>
<style>body{font-family:Arial,sans-serif;background:#eee;color:#17291b;margin:20px}nav{display:flex;justify-content:space-between;align-items:center;margin:20px 0}button{padding:10px 20px;cursor:pointer}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;max-width:1000px;margin:auto}article{background:#fff;border:1px dashed #777;padding:13px;break-inside:avoid;display:flex;flex-direction:column;align-items:flex-start;min-height:235px}header{font-weight:bold;font-size:12px;width:100%;display:flex;justify-content:space-between}header span{font-size:8px;font-weight:normal}h2{font-size:17px;margin:14px 0 7px}p{font-size:10px;line-height:1.5;margin:0 0 7px}img{width:72px;height:72px;float:left}strong{font-family:monospace;font-size:16px;letter-spacing:1px;margin:6px 0}small{font-size:8px;line-height:1.4}@page{size:A4;margin:10mm}@media print{body{margin:0;background:white}nav{display:none}.cards{gap:5mm}article{min-height:45mm;height:49mm;padding:3mm}h2{font-size:12px;margin:3mm 0 1mm}header{font-size:9px}p{font-size:8px;line-height:1.3;margin:0}img{height:17mm;width:17mm}strong{font-size:12px;margin:1mm 0}small{font-size:6px}}</style>
<nav><div><b>15 cartes · 5 trinômes</b><p>Hôte : HOST_URL. Réimprimez après configuration du réseau local.</p></div><button onclick="window.print()">Imprimer les cartes</button></nav><section class="cards">CARDS</section></html>'''
target = Path(__file__).resolve().parents[1] / "docs/cards.html"
target.write_text(page.replace("HOST_URL", html.escape(base)).replace("CARDS", "".join(items)))
print(f"Cartes générées : {target}")
