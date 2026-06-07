async def trigger_sync(connector_id: str) -> dict:
    return {"status": "stub", "message": "Fivetran MCP — implemented in Session 2"}


async def get_sync_status(connector_id: str) -> dict:
    return {"status": "stub", "last_sync": None}
