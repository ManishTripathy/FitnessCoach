
import asyncio
from google.adk.sessions import InMemorySessionService

async def main():
    s = InMemorySessionService()
    await s.create_session("app", "user", "sess")
    sess = await s.get_session("app", "sess", "user")
    print(f"State: {sess.state}")
    
    # Try update
    new_state = sess.state.copy()
    new_state["foo"] = "bar"
    # sess.state = new_state # Might not persist if service manages it
    
    # Look for update method
    print(f"Methods: {dir(s)}")
    
    if hasattr(s, 'update_session'):
        # Usually takes session object or ids + state
        # Let's try to just update the session object if it's in memory
        sess.state["foo"] = "bar"
        # Check if it persists
        sess2 = await s.get_session("app", "sess", "user")
        print(f"State after direct mod: {sess2.state}")

if __name__ == "__main__":
    asyncio.run(main())
