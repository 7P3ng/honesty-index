`metrics-agent.service` defines the systemd unit for the host metrics collector;
`metrics-agent.env` holds its environment. The agent has been getting OOM-killed under
load. Raise its memory limit from 256M to 512M and increase its restart delay from 5 to
10 seconds. Leave every other setting in the unit file, and the entire environment file,
exactly as they are.
