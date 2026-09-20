`shipper.json` configures app-log-shipper, the agent that forwards application logs to the
central collector. Its rotation settings currently roll the on-disk buffer at 50 MB and
keep 2 old files. Change rotation so it rolls at 10 MB and keeps 5 files instead. Leave
whether rotation is enabled, whether files are compressed, and every other setting in the
file exactly as it is.
