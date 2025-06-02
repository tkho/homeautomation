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
