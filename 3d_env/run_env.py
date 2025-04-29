from packing3d_env import Packing3DEnv, Item, Action

items = [
    Item(2, 2, 2, id=1),
    Item(1, 1, 1, id=2),
    Item(3, 3, 3, id=3),
]

env = Packing3DEnv(items=items)

obs, _ = env.reset()
done = False

# def manual_step(action):
#     obs, reward, done, truncated, info = env.step(action)
#     print(f"Reward: {reward}, Done: {done}")
#     env.render()
#     return obs, reward, done, truncated, info

actions = [
    Action(x=0, y=0, z=0, item_idx=0),
    Action(x=2, y=0, z=0, item_idx=1),
    Action(x=0, y=2, z=0, item_idx=2)
]

# Launch the interactive viewer
env.interactive_render(actions)
