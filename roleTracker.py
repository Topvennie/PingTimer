import asyncio
import json
from typing import Dict

from common_functions import get_unix_time


class RoleTracker:
    def __init__(self) -> None:
        self._json = False
        self._pinged_roles: Dict[int, list[int]] = {}

    async def read_file(self) -> Dict[str, Dict[str, list[str]]]:
        while self._json:
            await asyncio.sleep(1)
        self._json = True
        with open("roles.json", 'r') as f:
            data = json.load(f)
            f.close()

        self._json = False
        return data

    async def write_file(self, data: Dict[str, Dict[str, list[str]]]) -> None:
        while self._json:
            await asyncio.sleep(1)
        self._json = True
        with open("roles.json", 'w') as f:
            json.dump(data, f)
            f.close()

        self._json = False

    async def add_role(self, guild_id: int, role_id: int, time: int) -> None:
        data = await self.read_file()
        if str(guild_id) in data.keys():
            data[str(guild_id)][str(role_id)] = [str(time), str(get_unix_time())]
        else:
            data[str(guild_id)] = {str(role_id): [str(time), str(get_unix_time())]}
        await self.write_file(data)

    async def remove_role(self, guild_id: int, role_id: int) -> bool:
        data = await self.read_file()

        if str(guild_id) in data.keys() and str(role_id) in data[str(guild_id)].keys():
            del data[str(guild_id)][str(role_id)]
            if not data[str(guild_id)]:
                del data[str(guild_id)]
        else:
            return False

        await self.write_file(data)
        return True

    async def remove_guild(self, guild_id: int) -> None:
        data = await self.read_file()

        if str(guild_id) in data.keys():
            del data[str(guild_id)]

        await self.write_file(data)

    async def reset_role(self, guild_id: int, role_id: int) -> tuple[bool, bool]:
        data = await self.read_file()

        if str(guild_id) in data.keys() and str(role_id) in data[str(guild_id)].keys():
            if int(data[str(guild_id)][str(role_id)][1]) < get_unix_time():
                return True, False
            else:
                data[str(guild_id)][str(role_id)][1] = str(get_unix_time())
        else:
            return False, False

        await self.write_file(data)
        return True, True

    async def get_roles(self, guild_id: int) -> Dict[int, list[int]]:
        data = await self.read_file()

        if str(guild_id) not in data.keys():
            return {}

        result = {}
        guild_data = data[str(guild_id)]
        for role_id, values in guild_data.items():
            result[int(role_id)] = [int(value) for value in values]
        return result

    async def get_role(self, guild_id: int, role_id: int) -> bool:
        data = await self.read_file()

        return str(guild_id) in data.keys() and str(role_id) in data[str(guild_id)].keys()

    async def get_data(self) -> Dict[str, Dict[str, list[str]]]:
        return await self.read_file()

    def get_expired_ping_cooldowns(self) -> list[list[int]]:
        unix = get_unix_time()
        result = []
        for time, values in self._pinged_roles.items():
            if time < unix:
                result.append(values)

        return result

    async def ping_role(self, guild_id: int, role_id: int) -> None:
        data = await self.read_file()

        next_ping_time = get_unix_time() + int(data[str(guild_id)][str(role_id)][0])
        data[str(guild_id)][str(role_id)][1] = str(next_ping_time)
        for time, values in self._pinged_roles.items():
            if values[1] == role_id:
                del self._pinged_roles[time]
                break

        self._pinged_roles[next_ping_time] = [guild_id, role_id]

        await self.write_file(data)
