from packing3d_env import Packing3DEnv

env = Packing3DEnv()

obs, _ = env.reset()
done = False

while not done:
    # Try placing item at (0, 0, 0) every time just to test
    action = (0, 0, 0)
    obs, reward, done, truncated, info = env.step(action)
    print(f"Reward: {reward}, Done: {done}")
    env.render()
