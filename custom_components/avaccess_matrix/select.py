from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

OPTIONS = ["Input 1", "Input 2", "Input 3", "Input 4"]


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        MatrixOutputSelect(coordinator, entry, output)
        for output in range(1, 5)
    ]

    # 🔥 Important: ensures correct state on first load
    async_add_entities(entities, update_before_add=True)


class MatrixOutputSelect(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator, entry, output):
        super().__init__(coordinator)
        self._output = output
        self._entry = entry

        self._attr_name = f"HDMI Output {output}"
        self._attr_unique_id = f"{entry.entry_id}_output_{output}"
        self._attr_options = OPTIONS
        self._attr_icon = "mdi:video-switch"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"Matrix ({self.coordinator.host})",
            manufacturer="AV Access",
            model="4KMX44-H2",
            configuration_url=f"http://{self.coordinator.host}",
        )

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def current_option(self):
        value = self.coordinator.data.get(self._output)
        if value:
            return f"Input {value}"
        return None

    async def async_select_option(self, option: str):
        input_ = int(option.split(" ")[1])
        await self.coordinator.async_set_route(self._output, input_)
