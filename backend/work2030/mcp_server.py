"""Local stdio MCP server: no network, host access or external messaging tools."""
import os
from mcp.server.fastmcp import FastMCP
from .services import Services
from .store import Store, DomainError

mcp = FastMCP("WORK2030-local")
services = Services(Store())
bound_session = os.getenv("WORK2030_MCP_SESSION")


def invoke(name, session_id, args):
    if bound_session and session_id != bound_session:
        raise DomainError("Ce client MCP est lié à un autre trinôme")
    return services.call(name, session_id, args)


@mcp.tool()
def Memory(session_id: str, args: dict) -> dict:
    """Search fictional memory with provenance. args: query."""
    return invoke("Memory", session_id, args)


@mcp.tool()
def Resources(session_id: str, args: dict) -> dict:
    """Read available equipment and current assignments."""
    return invoke("Resources", session_id, args)


@mcp.tool()
def Space(session_id: str, args: dict) -> dict:
    """Read venues, capacities, accessibility and zones."""
    return invoke("Space", session_id, args)


@mcp.tool()
def Calendar(session_id: str, args: dict) -> dict:
    """Read availability or schedule after approval: operation=schedule, proposal_id."""
    return invoke("Calendar", session_id, args)


@mcp.tool()
def Budget(session_id: str, args: dict) -> dict:
    """Compute itemized budget: space_id, resource_ids."""
    return invoke("Budget", session_id, args)


@mcp.tool()
def Documents(session_id: str, args: dict) -> dict:
    """Produce an actual local Markdown document after approval: proposal_id."""
    return invoke("Documents", session_id, args)


@mcp.tool()
def Messaging(session_id: str, args: dict) -> dict:
    """Persist a fictional communication draft after approval. No external send."""
    return invoke("Messaging", session_id, args)


@mcp.tool()
def Workspace(session_id: str, args: dict) -> dict:
    """Read/preview/apply/complete the visual workspace. Mutations require approval."""
    return invoke("Workspace", session_id, args)


if __name__ == "__main__":
    mcp.run(transport="stdio")
