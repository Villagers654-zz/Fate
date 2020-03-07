import json
import sys
import psutil
from utils.utils import bytes2human as read

process = psutil.Process(int(sys.argv[1]))
interval = int(sys.argv[2])

memory_info = {
	"GLOBAL": {
		'RAM': {
			"USED": read(psutil.virtual_memory().used),
			"TOTAL": read(psutil.virtual_memory().total),
			"PERCENT": round(psutil.virtual_memory().percent)
		},
		"CPU": round(psutil.cpu_percent()),
		"STORAGE": {
			"USED": read(psutil.disk_usage('/').used),
			"TOTAL": read(psutil.disk_usage('/').total)
		}
	},
	"PID": {
		"CPU": round(process.cpu_percent(interval=interval)),
		"RAM": {
			"RSS": read(process.memory_full_info().rss),
			"PERCENT": round(process.memory_percent())
		}
	}
}

print(json.dumps(memory_info))
