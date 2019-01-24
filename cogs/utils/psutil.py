import psutil
import os

def bytes2human(n):
	symbols = ('GHz', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
	prefix = {}
	for i, s in enumerate(symbols):
		prefix[s] = 1 << (i + 1) * 10
	for s in reversed(symbols):
		if n >= prefix[s]:
			value = float(n) / prefix[s]
			return '%.1f%s' % (value, s)
	return "%sB" % n

# only shows results from startup or first use
p = psutil.Process(os.getpid())
pids = psutil.pids()
botram = p.memory_full_info().rss
ramused = psutil.virtual_memory().used
ramtotal = psutil.virtual_memory().total
rampercent = psutil.virtual_memory().percent
botcpu = p.cpu_percent(interval=1.0)
cpu = psutil.cpu_percent(interval=1.0)
percpu = psutil.cpu_percent(interval=1, percpu=True)
storageused = psutil.disk_usage('/').used
storagetotal = psutil.disk_usage('/').total
net = psutil.net_if_stats()
try:
	freq = bytes2human(psutil.cpu_freq().current)
except:
	freq = "unavailable"
try:
	freqmax = bytes2human(psutil.cpu_freq().max)
except:
	freqmax = "unavailable"
try:
	batterypercent = psutil.sensors_battery().percent
except:
	batterypercent = "unavailable"
try:
	if psutil.sensors_battery().power_plugged:
		ischarging = "charging"
except:
	ischarging = " "
try:
	temp = psutil.sensors_temperatures()
except:
	temp = "unavailable"
