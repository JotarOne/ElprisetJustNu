"""Config flow for Odum - ElprisetJustNu integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant import config_entries, core, data_entry_flow, exceptions
from .coordinator import FetchPriceCoordinator


from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(
            "price_area",
            default="SE2",
        ): vol.In(["SE1", "SE2", "SE3", "SE4"]),
        vol.Optional("transfer_fee", default=0): vol.Coerce(float),
        vol.Optional("energy_tax", default=0): vol.Coerce(float),
        vol.Optional("poll_time", default=60): vol.All(int, vol.Range(min=30)),
    }
        # vol.Optional("transfer_fee", default=0): vol.All(float, vol.Range(min=-10, max=5000)),
        # vol.Optional("poll_time", default=60): vol.All(int, vol.Range(min=30)),

)



async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""

    # hub = PlaceholderHub(data["host"])
    # if "username" in data and "password" in data:
    #     if not await hub.authenticate(data["username"], data["password"]):
    #         raise InvalidAuth

    # Return info that you want to store in the config entry.
    # return {"title": "Odum - ElPrisetJustNu"}
    return {"title": "Elpriset Just Nu"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Odum - ElprisetJustNu."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                uid = DOMAIN + "_" + user_input["price_area"]
                await self.async_set_unique_id(uid)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=info["title"] + " " + user_input["price_area"],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @core.callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlowWithConfigEntry):
    """Handle an options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Manage the options."""
        if user_input is not None:
            # return self.async_create_entry(data=user_input)
            if "price_area" in self.config_entry.data:
                user_input["price_area"] = self.config_entry.data["price_area"]
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input, options=self.config_entry.options
            )
            return self.async_create_entry(title="", data={})

        options_schema = vol.Schema(
            {
                vol.Optional("transfer_fee", default=self.config_entry.data.get("transfer_fee")): vol.Coerce(float),
                vol.Optional("energy_tax", default=self.config_entry.data.get("energy_tax")): vol.Coerce(float),
                vol.Optional("poll_time", default=self.config_entry.data.get("poll_time")): vol.All(int, vol.Range(min=30)),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                options_schema, self.config_entry.options
            ),
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
