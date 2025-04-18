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
        "away": 88.
    }
}

for zone, info in thermostats.items():
    entity_id = info["entity_id"]
    state = hass.states.get(entity_id)

    if not state:
        logger.warning(f"{zone.title()}: thermostat entity not found")
        continue

    current_temp = state.attributes.get("current_temperature")
    setpoint = state.attributes.get("temperature")

    if (action in ("decrease_1", "off")) and (setpoint is None or current_temp is None):
        logger.warning(f"{zone.title()}: missing temp data")
        continue

    if action == "decrease_1":
        new_temp = max(setpoint - 1, info["low"])
        if new_temp == setpoint:
            logger.warning(f"{zone.title()}: setpoint already at or below minimum ({info['low']})")
        else:
            logger.warning(f"{zone.title()}: lowering setpoint from {setpoint} → {new_temp}")
            hass.services.call("climate", "set_temperature", {
                "entity_id": entity_id,
                "temperature": new_temp,
                "hvac_mode": "cool"
            })

    elif action == "off":
        logger.warning(f"{zone.title()}: setting high/off temp {info['high']}")
        hass.services.call("climate", "set_temperature", {
            "entity_id": entity_id,
            "temperature": info["away"],
            "hvac_mode": "cool"
        })

    elif action == "on":
        logger.warning(f"{zone.title()}: restoring target temp to {info['low']}")
        hass.services.call("climate", "set_temperature", {
            "entity_id": entity_id,
            "temperature": info["high"],
            "hvac_mode": "cool"
        })

    else:
        logger.warning(f"{zone.title()}: unknown action '{action}'")
