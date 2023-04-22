from typing import Dict


class RoleTracker:
    def __init__(self) -> None:
        self.MAX_AMOUNT_OF_SERVERS = 100
        self.servers: Dict[int, Dict[int, list[int]]] = {}

    def add_role(self, guild_id: int, role_id: int, time: int) -> bool:
        raise NotImplementedError()

    def remove_role(self, guild_id: int, role_id: int) -> list[bool]:
        raise NotImplementedError()

    def remove_guild(self, guild_id: int) -> bool:
        raise NotImplementedError()

    def reset_role(self, guild_id: int, role_id: int) -> list[bool]:
        raise NotImplementedError()

    def get_roles(self, guild_id: int) -> Dict[int, list[int]]:
        raise NotImplementedError()

    def get_role(self, guild_id: int, role_id) -> bool:
        raise NotImplementedError()

    def ping_role(self, guild_id: int, role_id: int) -> bool:
        raise NotImplementedError()
