"""
 Controls HVAC thermostat behavior including temperature management and fan modes.

 Call this script using the `python_script.hvac_pre_cool_and_time_of_use` service
 and provide an "action" parameter via data.

 Supported Actions:
 ------------------

 General (applies to all zones):
   - "on"           : Set temperature to preset
   - "off"          : Set temperature to `away` value
   - "increase"     : Raise setpoint by 1°F
   - "decrease"     : Lower setpoint by 1°F
   - "increase_N"   : Raise setpoint by N°F
   - "decrease_N"   : Lower setpoint by N°F

 Fan Control:
   - "fan_on" / "fan_off"                         : Apply to all zones
   - "fan_on_upstairs" / "fan_off_downstairs"     : Apply to specific zone

 Fan Modes Used:
   - ON  = "Low"
   - OFF = "Auto low"
"""

def handle_hvac_action(data):
    action = data.get("action")
    logger.warning(f"HVAC script triggered with action: {action}")

    thermostats = {
        "downstairs": {
            "entity_id": "climate.thermostat",
            "low": float(hass.states.get("input_number.thermostat_downstairs_low").state),
            "high": float(hass.states.get("input_number.thermostat_downstairs_high").state),
            "away": 85.
        },
        "upstairs": {
            "entity_id": "climate.thermostat_2",
            "low": float(hass.states.get("input_number.thermostat_upstairs_low").state),
            "high": float(hass.states.get("input_number.thermostat_upstairs_high").state),
            "away": 87.
        }
    }

    def set_fan_mode(zone, mode):
        info = thermostats.get(zone)
        if not info:
            logger.warning(f"{zone.title()}: Zone not found")
            return
        entity_id = info["entity_id"]
        logger.warning(f"{zone.title()}: Setting fan mode to {mode}")
        hass.services.call("climate", "set_fan_mode", {
            "entity_id": entity_id,
            "fan_mode": mode
        }, blocking=True)

    if action.startswith("fan_"):
        parts = action.split("_")
        mode = parts[1]  # "on" or "off"
        target = parts[2] if len(parts) > 2 else "all"
        fan_mode = "Low" if mode == "on" else "Auto low"

        if target == "all":
            for zone in thermostats:
                set_fan_mode(zone, fan_mode)
        else:
            set_fan_mode(target, fan_mode)

        return

    # Normal thermostat temperature check logic
    for zone, info in thermostats.items():
        entity_id = info["entity_id"]
        state = hass.states.get(entity_id)

        if not state:
            logger.warning(f"{zone.title()}: thermostat entity not found")
            continue

        current_temp = state.attributes.get("current_temperature")
        setpoint = state.attributes.get("temperature")

        if (setpoint is None or current_temp is None) and (
            action.startswith("increase") or action.startswith("decrease") or action == "off"
        ):
            logger.warning(f"{zone.title()}: missing temp data")
            continue

        if action.startswith("increase") or action.startswith("decrease"):
            if "_" in action:
                _, amount_str = action.split("_", 1)
                delta = int(amount_str) if amount_str.isdigit() else None
            else:
                delta = 1

            if delta is None:
                logger.warning(f"{zone.title()}: invalid increase/decrease value")
                continue

            if action.startswith("decrease"):
                delta = -delta

            new_temp = setpoint + delta
            new_temp = max(info["low"], min(new_temp, info["away"]))

            if new_temp == setpoint:
                logger.warning(f"{zone.title()}: setpoint unchanged (already at limit)")
            else:
                logger.warning(f"{zone.title()}: adjusting setpoint from {setpoint} → {new_temp}")
                hass.services.call("climate", "set_temperature", {
                    "entity_id": entity_id,
                    "temperature": new_temp,
                    "hvac_mode": "cool"
                })

        elif action == "off":
            logger.warning(f"{zone.title()}: setting away temp {info['away']}")
            hass.services.call("climate", "set_temperature", {
                "entity_id": entity_id,
                "temperature": info["away"],
                "hvac_mode": "cool"
            })

        elif action == "on":
            logger.warning(f"{zone.title()}: restoring target temp to {info['high']}")
            hass.services.call("climate", "set_temperature", {
                "entity_id": entity_id,
                "temperature": info["high"],
                "hvac_mode": "cool"
            })

        else:
            logger.warning(f"{zone.title()}: unknown action '{action}'")

handle_hvac_action(data)
