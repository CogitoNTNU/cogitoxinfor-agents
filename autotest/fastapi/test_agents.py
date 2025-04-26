import asyncio
import random

import aiohttp


async def test_agent(session, agent_id, task):
	# Start agent
	async with session.post('http://localhost:8000/agent/run', json={'agent_id': f'agent_{agent_id}', 'task': task}) as response:
		print(f'Started agent_{agent_id}:', await response.json())

	# Monitor status
	while True:
		async with session.get(f'http://localhost:8000/agent/{agent_id}/status') as response:
			status = (await response.json())['status']
			print(f'Agent {agent_id} status:', status)
			if status in ['stopped', 'error']:
				break
		await asyncio.sleep(2)


async def main():
	tasks = [
		'Search for Python programming tutorials',
		'Find information about machine learning',
		'Look up web development resources',
		'Research data science tools',
		'Find AI programming examples',
		'Search for software testing methods',
		'Look up database optimization techniques',
		'Research cloud computing platforms',
		'Find cybersecurity best practices',
		'Search for DevOps tutorials',
	]
	tasks = tasks * 10

	async with aiohttp.ClientSession() as session:
		# Start 10 agents simultaneously
		agent_tasks = [test_agent(session, i, tasks[i]) for i in range(50)]
		await asyncio.gather(*agent_tasks)


if __name__ == '__main__':
	asyncio.run(main())
