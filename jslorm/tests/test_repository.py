import asyncio
import pytest
from jslorm import Database, BaseModel, BaseRepository

class TestUser(BaseModel):
    name: str
    email: str
    __table_name__ = "test_users"

@pytest.mark.asyncio
async def test_create_user():
    db = Database("test_db")
    repo = BaseRepository(db.driver, TestUser)
    await repo.create_table()
    
    user = TestUser(name="Test", email="test@example.com")
    saved_user = await repo.create(user)
    
    assert saved_user.id is not None
    assert saved_user.name == "Test"
    assert saved_user.email == "test@example.com"

@pytest.mark.asyncio
async def test_find_user():
    db = Database("test_db")
    repo = BaseRepository(db.driver, TestUser)
    
    users = await repo.find({"name": "Test"})
    assert len(users) > 0
    assert users[0].name == "Test"