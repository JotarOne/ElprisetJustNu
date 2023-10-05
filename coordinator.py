"""The data update coordinator for ElprisetJustNu."""
from datetime import datetime, timedelta
import json
import logging
from typing import cast

from dateutil.tz import gettz

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from collections.abc import Mapping
from typing import Any


from .const import (
    API_URL,
    DEVICE_IDENTIFIER,
    DOMAIN,
    VAL_CURRENT_PRICE,
    VAL_DAY_AVERAGE_PRICE,
    DEFAULT_NAME,
    FEES
)
from .elprisetjustnu_client import ElprisetJustNuClient

_LOGGER = logging.getLogger(__name__)


class FetchPriceCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data."""

    config_entry: ConfigEntry
    sensor_data: dict

    def __init__(
        self,
        hass: HomeAssistant,
        epjn_api: ElprisetJustNuClient,
        config_entry: ConfigEntry,
        fetch_interval: timedelta,
        sensor_data: dict,
        entry_data: Mapping[str, Any],
    ) -> None:
        # self.data = {}
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=DOMAIN,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=10),
        )
        self.sensor_data = sensor_data
        self.config_entry = config_entry
        self.epjn_api = epjn_api
        self.epjn_data_today = ""
        self.entry_prefix = "elprisetjustnu"
        self.fetch_interval = fetch_interval
        self.current_data: list[ElprisetJustNuClient.PriceInfo] = []
        self.entry_data = entry_data

        self.last_fetch = datetime.now()
        self.price_area = entry_data["price_area"]

    async def _async_update_data(self):
        """Update data via library."""

        await self.checkData()
        return self.sensor_data

    async def forceUpdate(self):
        """Force update data via library."""
        self.current_data = None
        self.async_refresh()

    def getPrices(self) -> list[dict]:
        dteToday: datetime = datetime.now(gettz(self.hass.config.time_zone))
        ret = list[dict]()
        if self.current_data is not None and len(self.current_data) > 0:
            for x in reversed(self.current_data):
                if x.dte >= dteToday.date():
                    for p in x.prices:
                        ret.append({"date": (datetime.combine(x.dte, datetime.min.time()) + timedelta(hours=p.hour)).strftime("%Y-%m-%d %H:%M:%S"), "value": p.price})
                        # ret[(datetime.combine(x.dte, datetime.min.time()) + timedelta(hours=p.hour)).strftime("%Y-%m-%d %H:%M:%S")] = p.price

        return ret

    async def checkData(self):
        """Check data validity."""
        dteToday: datetime = datetime.now(gettz(self.hass.config.time_zone))
        fetched = False
        if self.current_data is None or len(self.current_data) == 0:
            self.current_data = await self.epjn_api.fetchData(
                dteToday.date(), self.price_area
            )
            self.last_fetch = datetime.now()
            fetched = True

        if self.current_data is not None and len(self.current_data) > 0:
            if not fetched and (datetime.now() - self.last_fetch) > self.fetch_interval:
                tmp_data = await self.epjn_api.fetchData(
                    dteToday.date(), self.price_area
                )
                fetched = True
                if tmp_data is not None:
                    self.current_data = tmp_data

            d: ElprisetJustNuClient.PriceInfo
            d = next((x for x in self.current_data if x.dte == dteToday.date()), None)
            gotToday = d is not None
            needTomorrow = False

            if datetime.now().hour > 13:
                # check for tomorrows values
                d = next(
                    (
                        x
                        for x in self.current_data
                        if x.dte == (dteToday.date() + timedelta(days=1))
                    ),
                    None,
                )
                if d is None:
                    needTomorrow = True

            if not fetched and (needTomorrow or not gotToday):
                self.current_data = await self.epjn_api.fetchData(
                    dteToday.date(), self.price_area
                )
                fetched = True

            if fetched:
                self.last_fetch = datetime.now()

            if len(self.current_data) > 0:
                try:
                    found = False
                    for d in self.current_data:
                        if d.dte == dteToday.date():
                            self.getPricesFromPriceInfo(d, dteToday)
                            found = True
                            break

                    if not found:
                        self.getPricesFromPriceInfo(self.current_data[0], dteToday)

                except json.JSONDecodeError as err:
                    _LOGGER.error("Error %s", err)

    def getPricesFromPriceInfo(
        self, d: ElprisetJustNuClient.PriceInfo, dteToday: datetime
    ) -> None:
        """Set sensor data values."""
        if len(d.prices) > 0:
            p = next((x for x in d.prices if x.hour == dteToday.hour), None)
            if p is not None:
                self.sensor_data[VAL_CURRENT_PRICE] = round(p.price, 5)
            else:
                self.sensor_data[VAL_CURRENT_PRICE] = round(d.prices[-1].price, 5)
        else:
            self.sensor_data[VAL_CURRENT_PRICE] = 0

        self.sensor_data[VAL_DAY_AVERAGE_PRICE] = round(d.day_average, 5)

    @property
    def device_info(self) -> DeviceInfo:
        """Device info."""
        cast(str, self.config_entry.unique_id)
        configuration_url = API_URL

        return DeviceInfo(
            identifiers={
                (DEVICE_IDENTIFIER, DOMAIN + "_" + self.price_area),
            },
            manufacturer="Odum",
            name=DEFAULT_NAME + " " + self.price_area,
            configuration_url=str(configuration_url),
        )
    @property
    def fees(self) -> float:
        # return self.transfer_fee + self.energy_tax
        tf: float = 0
        et: float = 0
        if "transfer_fee" in self.entry_data:
            tf = self.entry_data["transfer_fee"]
        if "energy_tax" in self.entry_data:
            et = self.entry_data["energy_tax"]

        return (tf * 0.01) + (et * 0.01)