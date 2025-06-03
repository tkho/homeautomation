# Pre-cooling

Home Assistant automation + python_script for cooling around time-of-use rates.

* active May to September
  * Note: NV Energy TOU peak is June to September, 6 to 9pm
* off from 5:55pm - 9:05pm
* at 9:05, cooling set to 79 degrees -- the high-end-of-comfort
* slowly cools to 76 starting at 1am to when it's higher HVAC efficiency.