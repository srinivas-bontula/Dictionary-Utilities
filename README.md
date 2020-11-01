# Dictionary-Utilities
Utilities for a python dictionary

Methods 

- getpath -> Gets the value following the path list, if the path doesn't exitst returns the default value
- convert_values_to_string -> converts all dict values to string
- whitelist_dict -> Whitelist data according to the list of elements passed in. Data keys not in whitelist and present should be redacted.
- traverse_range_key_dict -> Returns the value if given member(strictly integer) is found within the range of the dictionary key range else returns None
- _recursive_mask_values -> Recursively finds keys of the names specified and replaces the corresponding values with 'X'.
- _recursively_alter_values_in_dict -> Recursively finds keys of the names specified and massages the corresponding values with the function that is passed as the parameter.

Class
- LoggedDict -> This class wraps a dict to figure out how that dict is being used
- Bunch -> A dot-accessible dictionary (a la JavaScript objects)
