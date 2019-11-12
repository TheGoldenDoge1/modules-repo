# -*- coding: future_fstrings -*-

#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .. import loader, utils

import logging
import datetime
import time

logger = logging.getLogger(__name__)


def register(cb):
    cb(AFKMod())


class AFKMod(loader.Module):
    """Provides a message saying that you are unavailable"""

    def __init__(self):
        self.name = _("AFK")
        self._me = None
        self._ratelimit = []

    async def client_ready(self, client, db):
        self._db = db
        self._me = await client.get_me()

    async def afkcmd(self, message):
        """.afk [message]"""
        if utils.get_args_raw(message):
            self._db.set(__name__, "afk", utils.get_args_raw(message))
        else:
            self._db.set(__name__, "afk", True)
        self._db.set(__name__, "gone", time.time())
        await self.allmodules.log("afk", data=utils.get_args_raw(message) or None)
        await utils.answer(message, _("<code>Ma owner's goin' AFK</code>"))

    async def unafkcmd(self, message):
        """Remove the AFK status"""
        self._ratelimit.clear()
        self._db.set(__name__, "afk", False)
        self._db.set(__name__, "gone", None)
        await self.allmodules.log("unafk")
        await utils.answer(message, _("<code>My owner's no longer AFK</code>"))

    async def watcher(self, message):
        if message.mentioned or getattr(message.to_id, "user_id", None) == self._me.id:
            logger.debug("tagged!")
            if message.from_id in self._ratelimit:
                self._ratelimit.remove(message.from_id)
                return
            else:
                self._ratelimit += [message.from_id]
            user = await utils.get_user(message)
            if user.is_self or user.bot or user.verified:
                logger.debug("User is self, bot or verified.")
                return
            if self.get_afk() is False:
                return
            now = datetime.datetime.now().replace(microsecond=0)
            gone = datetime.datetime.fromtimestamp(self._db.get(__name__, "gone")).replace(microsecond=0)
            diff = now - gone
            if self.get_afk() is True:
                ret = _("My owner is AFK right now (since {} ago).").format(diff)
            elif self.get_afk() is not False:
                ret = _("My owner is AFK right now (since {} ago).\nReason: <i>{}</i>").format(diff, self.get_afk())
            await utils.answer(message, ret)

    def get_afk(self):
        return self._db.get(__name__, "afk", False)
