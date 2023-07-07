#  Copyright 2021-present, the Recognai S.L. team.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from argilla.client.api import ArgillaSingleton
from argilla.client.sdk.v1.workspaces.models import WorkspaceModel
from argilla.client.users import User

if TYPE_CHECKING:
    from argilla.server.models import User as ServerUser

from tests.factories import UserFactory, WorkspaceFactory, WorkspaceUserFactory


def test_user_cls_init() -> None:
    with pytest.raises(
        Exception,
        match=r"`User` cannot be initialized via the `__init__` method | you should use `User.from_name\('test_user'\)`",
    ):
        User(name="test_user")

    with pytest.raises(
        Exception,
        match=r"`User` cannot be initialized via the `__init__` method | you should use `User.from_id\('00000000-0000-0000-0000-000000000000'\)`",
    ):
        User(id="00000000-0000-0000-0000-000000000000")


@pytest.mark.asyncio
async def test_user_from_name(owner: "ServerUser") -> None:
    new_user = await UserFactory.create(username="test_user")
    ArgillaSingleton.init(api_key=owner.api_key)

    user = User.from_name(new_user.username)
    assert user.username == new_user.username
    assert isinstance(user.id, UUID)

    with pytest.raises(ValueError, match="User with username="):
        User.from_name("non-existing-user")


@pytest.mark.asyncio
async def test_user_from_id(owner: "ServerUser") -> None:
    new_user = await UserFactory.create(username="test_user")
    ArgillaSingleton.init(api_key=owner.api_key)

    user = User.from_id(id=new_user.id)
    assert user.username == "test_user"
    assert isinstance(user.id, UUID)

    with pytest.raises(ValueError, match="User with id="):
        User.from_id(id="00000000-0000-0000-0000-000000000000")


def test_user_me(owner: "ServerUser") -> None:
    ArgillaSingleton.init(api_key=owner.api_key)

    user = User.me()
    assert user.id == owner.id
    assert user.username == owner.username


def test_user_create(owner: "ServerUser") -> None:
    ArgillaSingleton.init(api_key=owner.api_key)

    with pytest.warns(UserWarning):
        new_user = User.create("test_user", password="test_password")
        assert new_user.username == "test_user"

    with pytest.raises(ValueError, match="already exists in Argilla"):
        User.create("test_user", password="test_password")


@pytest.mark.asyncio
async def test_user_list(owner: "ServerUser") -> None:
    await UserFactory.create(username="user_1")
    await UserFactory.create(username="user_2")
    ArgillaSingleton.init(api_key=owner.api_key)

    users = User.list()
    assert all(user.username in ["user_1", "user_2", owner.username] for user in users)


@pytest.mark.asyncio
async def test_user_delete_user(owner: "ServerUser") -> None:
    new_user = await UserFactory.create(username="test_user")
    ArgillaSingleton.init(api_key=owner.api_key)

    user = User.from_name("test_user")
    assert user.username == new_user.username

    user.delete()
    with pytest.raises(ValueError, match="doesn't exist in Argilla"):
        user.delete()


def test_user_repr(owner: "ServerUser") -> None:
    ArgillaSingleton.init(api_key=owner.api_key)

    assert str(User.me()) == (
        f"User(id={owner.id}, username={owner.username}, role={owner.role.value},"
        f" workspaces={owner.workspaces}, api_key={owner.api_key}, first_name={owner.first_name},"
        f" last_name={owner.last_name}, role={owner.role}, inserted_at={owner.inserted_at},"
        f" updated_at={owner.updated_at})"
    )


@pytest.mark.asyncio
async def test_user_workspaces(owner: "ServerUser") -> None:
    workspaces = await WorkspaceFactory.create_batch(3)
    for workspace in workspaces:
        await WorkspaceUserFactory.create(workspace_id=workspace.id, user_id=owner.id)
    ArgillaSingleton.init(api_key=owner.api_key)

    user = User.me()
    assert isinstance(user.workspaces, list)
    assert len(user.workspaces) == len(workspaces)
    assert all(isinstance(workspace, WorkspaceModel) for workspace in user.workspaces)
    assert [workspace.name for workspace in workspaces] == [workspace.name for workspace in user.workspaces]