from __future__ import annotations

from app.mcp.tool_service import MCPToolService

try:
    from mcp.server.fastmcp import FastMCP
except Exception as exc:  # pragma: no cover - runtime dependency guard
    FastMCP = None
    _mcp_import_error = exc
else:
    _mcp_import_error = None


def create_mcp_server() -> "FastMCP":
    if FastMCP is None:
        raise RuntimeError(
            "MCP dependency is not installed. Install project dependencies first (including 'mcp')."
        ) from _mcp_import_error

    service = MCPToolService()
    mcp = FastMCP("AeroInsight RAG MCP Server")

    @mcp.tool(
        name="list_concepts",
        description="List aerodynamic concepts with optional status filter and pagination.",
    )
    def list_concepts(status: str | None = None, page: int = 1, page_size: int = 20) -> dict:
        return service.list_concepts(status=status, page=page, page_size=page_size)

    @mcp.tool(
        name="create_concept",
        description="Create a new aerodynamic concept for later RAG evaluation.",
    )
    def create_concept(
        title: str,
        description: str,
        author: str | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        return service.create_concept(
            title=title,
            description=description,
            author=author,
            tags=tags,
        )

    @mcp.tool(
        name="evaluate_concept",
        description="Run full RAG + LLM evaluation for a concept id.",
    )
    def evaluate_concept(concept_id: int) -> dict:
        return service.evaluate_concept(concept_id=concept_id)

    @mcp.tool(
        name="get_evaluation",
        description="Retrieve the stored evaluation (and retrieved literature context) for a concept.",
    )
    def get_evaluation(concept_id: int) -> dict:
        return service.get_evaluation(concept_id=concept_id)

    return mcp


def main() -> None:
    mcp = create_mcp_server()
    mcp.run()


if __name__ == "__main__":
    main()
