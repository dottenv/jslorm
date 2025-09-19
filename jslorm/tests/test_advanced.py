import asyncio
import pytest
from jslorm import Database, BaseModel, BaseRepository, Operator, foreign_key

class User(BaseModel):
    name: str
    email: str
    age: int
    
    __table_name__ = "users"
    __indexes__ = ["email"]
    __unique_fields__ = ["email"]

class Post(BaseModel):
    title: str
    content: str
    user_id: int = foreign_key("users")
    
    __table_name__ = "posts"

@pytest.mark.asyncio
async def test_advanced_queries():
    db = Database("test_advanced")
    user_repo = BaseRepository(db.driver, User)
    await user_repo.create_table()
    
    # Create test users
    await user_repo.create(User(name="John", email="john@test.com", age=25))
    await user_repo.create(User(name="Jane", email="jane@test.com", age=30))
    await user_repo.create(User(name="Bob", email="bob@test.com", age=20))
    
    # Test operators
    adults = await user_repo.find(age__gte=25)
    assert len(adults) == 2
    
    young_users = await user_repo.find(age__lt=25)
    assert len(young_users) == 1
    
    johns = await user_repo.find(name__like="John")
    assert len(johns) == 1
    
    # Test aggregations
    total_users = await user_repo.count()
    assert total_users == 3
    
    avg_age = await user_repo.avg("age")
    assert avg_age == 25.0

@pytest.mark.asyncio
async def test_query_builder():
    db = Database("test_builder")
    
    query = db.query("users").where("age", Operator.GT, 18).order_by("name").limit(10)
    
    # Test query structure
    query_dict = query.to_dict()
    assert len(query_dict["where"]) == 1
    assert query_dict["where"][0]["operator"] == Operator.GT
    assert query_dict["limit"] == 10

@pytest.mark.asyncio
async def test_relationships():
    db = Database("test_relations")
    user_repo = BaseRepository(db.driver, User)
    post_repo = BaseRepository(db.driver, Post)
    
    await user_repo.create_table()
    await post_repo.create_table()
    
    # Create user and post
    user = await user_repo.create(User(name="Author", email="author@test.com", age=28))
    post = await post_repo.create(Post(title="Test Post", content="Content", user_id=user.id))
    
    # Verify relationship
    assert post.user_id == user.id
    
    # Find posts by user
    user_posts = await post_repo.find(user_id=user.id)
    assert len(user_posts) == 1

@pytest.mark.asyncio
async def test_performance_features():
    db = Database("test_performance", enable_compression=True)
    
    # Test metrics
    metrics = await db.get_metrics()
    assert "queries" in metrics
    assert "total_time" in metrics
    
    # Test health check
    health = await db.health_check()
    assert health["status"] in ["healthy", "unhealthy"]