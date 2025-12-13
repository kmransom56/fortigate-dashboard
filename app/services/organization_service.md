# organization_service.md

## Purpose
The `organization_service.py` acts as a high-level abstraction layer for managing a multi-tenant, multi-brand enterprise. It is designed to be the central point of control and information for an environment that includes different restaurant brands (Sonic, Buffalo Wild Wings, Arby's), each with potentially different network infrastructure types. The service provides a unified way to view the entire enterprise, get summaries, and initiate large-scale operations like device discovery.

## Dependencies
- **`logging`**: For application-level logging.
- **`Enum`**: Used to create strongly-typed enumerations for `RestaurantBrand`, `InfrastructureType`, and `LocationStatus`, which helps prevent errors and makes the code more readable.
- **`dataclasses`**: To create the `Organization` and `Location` data classes, providing a clear and structured way to represent these entities.
- **`asyncio`**: Used to simulate asynchronous operations in the `discover_organization_devices` method.
- **`datetime`**: For handling timestamps.

## API

### `get_organization_service() -> OrganizationService`
A factory function that provides a singleton instance of the `OrganizationService`, ensuring that the enterprise data is loaded once and shared consistently.

### `OrganizationService` Class
This class holds the data and business logic for the entire enterprise.

#### `get_organization(org_id: str) -> Optional[Organization]`
Retrieves the data for a single organization (e.g., "sonic") by its ID.

#### `get_organization_locations(org_id: str) -> List[Location]`
Returns a list of all locations associated with a specific organization.

#### `get_enterprise_summary() -> Dict[str, Any]`
Calculates and returns a high-level summary of the entire enterprise, including the total number of locations and estimated counts of different device types (FortiGates, switches, APs, etc.).

#### `get_organization_discovery_config(org_id: str) -> Dict[str, Any]`
Provides a tailored configuration for running a device discovery process on a specific organization. The configuration, including which discovery methods to use, is determined by the organization's infrastructure type (e.g., "fortinet_full" vs. "fortinet_meraki").

#### `get_compliance_requirements(org_id: str) -> Dict[str, Any]`
Returns a dictionary of industry and brand-specific compliance standards (like PCI-DSS) that apply to a given organization.

#### `discover_organization_devices(org_id: str) -> Dict[str, Any]`
An `async` method that simulates the process of running a device discovery task across all locations within an organization. In a real-world implementation, this would be the entry point for kicking off a large-scale, distributed discovery process.

## Configuration
Currently, all data in this service is **hardcoded**. The lists of organizations, sample locations, and API rate limits are defined directly within the service's `_load_*` methods. In a production environment, this data would be externalized and loaded from a database or a set of configuration files.

## Data Flow
1. The `OrganizationService` is instantiated and immediately loads its hardcoded data (organizations, locations, etc.) into memory.
2. Other parts of the application can then call the service's methods to get information about the enterprise.
3. For example, calling `get_enterprise_summary()` will cause the service to iterate through its in-memory list of organizations and calculate the summary statistics.
4. When a method like `discover_organization_devices()` is called, the service retrieves the relevant organization and its locations from memory and then simulates an asynchronous discovery process.

## Error Handling
- The service's methods that perform lookups (e.g., `get_organization`) return `Optional` types, which is a clean way to handle cases where a requested item is not found.
- The `discover_organization_devices` simulation includes a `try...except` block to catch and record any errors that might occur during the process.

## Testing
This file does not contain its own unit tests. To test this service, one would instantiate the `OrganizationService` and write assertions to verify that the various `get_*` methods return the expected hardcoded data. Testing the `discover_organization_devices` method would require an `async` test runner (like `pytest-asyncio`) and would likely involve mocking the `_discover_location_devices` helper method to control the simulation.
