import sys
sys.path.insert(0, r'C:\Users\Edu\Documents\ClaudeWork\KeplerDB')
import kepler_interp as ki

# test directo get_planeta
rows = ki.get_planeta('Sol', 'Libra', 5)
print('get_planeta Sol Libra casa5:', rows)

rows2 = ki.get_planeta('Luna', 'Tauro', 12)
print('get_planeta Luna Tauro casa12:', rows2)
