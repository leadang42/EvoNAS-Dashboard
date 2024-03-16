import json

##########################################################################################

# MODULE SEARCH SPACE

# The Search Space Module provides functionalities for defining, managing, and exploring 
# search spaces in the context of evolutionary neural network architectures.
# It offers tools to represent the possible configurations, constraints, and relationships 
# between components within a predefined solution space.

###########################################################################################


### READ DATA FROM SEARCH SPACE JSON ###

def json_to_dict(filepath):
    """
    Convert JSON data from a file to a Python dictionary.

    Parameters:
        filepath (str): The path to the JSON file.

    Returns:
        dict: A Python dictionary representing the JSON data.

    Raises:
        FileNotFoundError: If the specified file is not found.
        json.JSONDecodeError: If there is an issue decoding the JSON data.

    Example:
    >>> data = json_to_dict('example.json')
    """
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {filepath}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Error decoding JSON data in file {filepath}: {e}")

def get_search_space(run):
    """
    Retrieve the search space configuration from a JSON file for a specific run.

    Parameters:
        run (str): The identifier for the run. This is used to construct the path to the search_space.json file.

    Returns:
        dict: A Python dictionary representing the search space configuration for the specified run.

    Raises:
        FileNotFoundError: If the search_space.json file for the given run is not found.
        json.JSONDecodeError: If there is an issue decoding the JSON data in the search_space.json file.

    Example:
    >>> search_space = get_search_space('evonas_run')
    """
    return json_to_dict(f"../data/{run}/search_space.json")

def get_groups(run):
    """
    Extract and organize layer groups from the search space configuration for a specific run.

    Parameters:
        run (str): The identifier for the run. This is used to construct the path to the search_space.json file.

    Returns:
        dict: A dictionary where keys are group types, and values are lists of layer identifiers belonging to each group.

    Raises:
        KeyError: If the expected keys ('gene_pool', 'layer', 'group') are not present in the search space data.
        TypeError: If the data structure of the search space is not as expected.

    Example:
    >>> layer_groups = get_groups('evonas_run')
    """
    search_space = get_search_space(run)
    layer_dict = {}

    for layer_info in search_space.get("gene_pool", []):
        layer_id = layer_info.get("layer")
        group_type = layer_info.get("group")

        if layer_id is not None and group_type is not None:
            if group_type not in layer_dict:
                layer_dict[group_type] = []

            layer_dict[group_type].append(layer_id)
        else:
            raise KeyError("Expected keys ('gene_pool', 'layer', 'group') not found or have None values.")
    print("\nGet groups: ", layer_dict)
    return layer_dict
    
    
### GRAPH CREATED FROM RULESETS ### 
            
def get_layer_graph(run, group_connections=True):
    """
    Retrieves the layer graph based on the search space defined for a given run.

    Args:
        run (str): The identifier for the run. This is used to construct the path to the search_space.json file.
        group_connections (bool, optional): If True, includes group connections in the graph. 
            Defaults to True.

    Returns:
        dict: A dictionary representing the layer graph. Keys are source layers, 
              and values are lists of target layers connected to the source layer.

    Raises:
        KeyError: If the expected keys ('rule_set', 'allowed_after', 'layer', 'rule_set_groups', 'group') are not present in the search space data.
        TypeError: If the data structure of the search space is not as expected.

    Example:
        >>> get_layer_graph("run_123")
        {'STFT_2D': ['MAG_2D'], 'MAG_2D': ['FB_2D'], 'FB_2D': ['C_2D', 'DC_2D', 'MAG2DEC_2D'], ...}
    """
    try:
        # Read search space from JSON
        search_space = get_search_space(run)

        # Store layer connections in dictionary
        graph = {}

        # Process layers connections
        for layer_rule in search_space.get("rule_set", []):
            if not (layer_rule.get("exclude", False)):
                
                # Identify source and target layers
                src_layer = layer_rule["layer"]
                target_layers = layer_rule["allowed_after"]
                graph[src_layer] = target_layers

        print("\nBefore groups: ", graph)
        
        # Return graph without group connections
        if not group_connections:
            return graph       

        # Process group connections
        for group_rule in search_space.get("rule_set_groups", []):
            
            # Identify source and target group
            for target_group in group_rule.get("allowed_after", []):
                source_groups = group_rule.get("group", [])

                # Identify source and target layers in source and target groups
                groups = get_groups(run)
                source_layers = groups.get(source_groups, [])
                target_layers = groups.get(target_group, [])

                for src_layer in source_layers:
                    if src_layer in graph:
                        graph[src_layer] += target_layers
                    else:
                        graph[src_layer] = target_layers

        print("\nAfter groups: ",graph)
        return graph

    except KeyError as key_error:
        raise KeyError(f"Expected key not found in search space data: {key_error}")

    except TypeError as type_error:
        raise TypeError(f"Unexpected data structure in search space data: {type_error}")

def get_group_graph(run):
    """
    Builds the group graph based on the search space defined for a given run.

    Args:
        run (str): The identifier for the run. This is used to construct the path to the search_space.json file.

    Returns:
        dict: A dictionary representing the group graph. Keys are source groups, 
              and values are lists of target groups connected to the source group.

    Raises:
        KeyError: If the expected keys ('rule_set_groups', 'allowed_after', 'group') are not present in the search space data.
        TypeError: If the data structure of the search space is not as expected.

    Example:
        >>> get_group_graph("run_123")
        {'Feature Extraction 1D': ['Global Pooling 1D'], 'Feature Extraction 2D': ['Global Pooling 2D']}
    """
    try:
        # Read search space from JSON
        search_space = get_search_space(run)

        # Store groups connections in dictionary
        group_graph = {}

        # Process group connections
        for group_rule in search_space.get("rule_set_groups", []):
            excluded = group_rule.get("exclude", False)

            if not excluded:
                # Identify source and target group
                source_group = group_rule["group"]
                target_groups = group_rule.get("allowed_after", [])
                group_graph[source_group] = target_groups
        
        return group_graph

    except KeyError as key_error:
        raise KeyError(f"Expected key not found in search space data: {key_error}")

    except TypeError as type_error:
        raise TypeError(f"Unexpected data structure in search space data: {type_error}")
 
 
### CONNECTED LAYERS ### 
  
def dfs(graph, layer, visited, result):
    """
    Perform depth-first search (DFS) on the given graph starting from the specified layer.

    Args:
        graph (dict): A dictionary representing the layer graph.
        layer (str): The starting layer for DFS.
        visited (set): A set to keep track of visited layers.
        result (list): A list to store the layers visited in DFS order.

    Returns:
        None

    Example:
        >>> graph = {'A': ['B', 'C'], 'B': ['D'], 'C': ['E'], 'D': [], 'E': []}
        >>> visited = set()
        >>> result = []
        >>> dfs(graph, 'A', visited, result)
        >>> print(result)
        ['A', 'B', 'D', 'C', 'E']
    """
    if layer not in visited:
        visited.add(layer)
        result.append(layer)

        for neighbor in graph.get(layer, []):
            dfs(graph, neighbor, visited, result)

def get_connected_layers(run, start_layer):
    """
    Retrieve layers connected to the specified starting layer in the layer graph for a given run.

    Args:
        run (str): The identifier for the run. This is used to construct the path to the search_space.json file.
        start_layer (str): The layer from which to start exploring connected layers.

    Returns:
        list: A list of layers connected to the starting layer.

    Raises:
        ValueError: If the specified start_layer is not found in the layer graph.

    Example:
        >>> get_connected_layers('run_123', 'STFT_2D')
        ['STFT_2D', 'MAG_2D', 'FB_2D', 'C_2D', 'DC_2D', 'MAG2DEC_2D', ...]
    """
    try:
        graph = get_layer_graph(run, group_connections=True)
        if start_layer not in graph:
            raise ValueError(f"The specified start_layer '{start_layer}' is not found in the layer graph.")

        visited = set()
        result = []

        dfs(graph, start_layer, visited, result)
        
        return result

    except KeyError as key_error:
        raise KeyError(f"Expected key not found in layer graph data: {key_error}")

    except TypeError as type_error:
        raise TypeError(f"Unexpected data structure in layer graph data: {type_error}")


### DASH CYTOSCAPE FORMAT ###

def get_node_element(gene):
    """
    Create a node element from a gene, representing a layer or group.

    Args:
        gene (dict): A dictionary representing a gene.

    Returns:
        dict: A dictionary representing a node element with appropriate attributes.

    Example:
        >>> gene = {'layer': 'STFT_2D', 'group': 'Feature Extraction 2D', 'exclude': False}
        >>> get_node_element(gene)
        {'id': 'STFT_2D', 'label': 'STFT 2D', 'parent': 'Feature Extraction 2D', 'layer': 'STFT_2D'}
    """
    layer = gene["layer"]
    node = gene.copy()

    # Assigning ID and label based on the layer
    node["id"] = layer
    node["label"] = layer.replace("_", " ")

    # Group is optional
    if "group" in gene:
        # If group is present, move it to 'parent' and remove it from the node itself
        group = node.pop("group")
        node["parent"] = group

    return node

def get_cytoscape_elements(run):
    """
    Create Cytoscape elements representing layers and group connections in the search space for a given run.

    Args:
        run (str): The identifier for the run. This is used to construct the path to the search_space.json file.

    Returns:
        tuple: A tuple containing a list of Cytoscape elements and a list of unique group names.

    Raises:
        KeyError: If the expected keys ('gene_pool') are not present in the search space data.
        TypeError: If the data structure of the search space is not as expected.

    Example:
        >>> get_cytoscape_elements('run_123')
        ([{'data': {'id': 'Start', 'label': 'Start', 'f_name': 'Start', 'layer': 'Start'}},
          {'data': {'id': 'Feature Extraction 2D', 'label': 'Feature Extraction 2D', 'parent': 'Feature Extraction 2D'}},
          ...
         ],
         ['Feature Extraction 2D', ...])
    """
    try:
        # Retrieve search space data
        search_space = get_search_space(run)

        # Initialize elements with a start node
        elements = [{'data': {'id': 'Start', 'label': 'Start', 'f_name': 'Start', 'layer': 'Start'}}]
        group_elements = []
        groups = []

        # Use connected layers to create nodes of layers and groups
        start_layer = "Start"
        connected_layers = get_connected_layers(run, start_layer)
        genes = search_space.get("gene_pool", [])

        for gene in genes:
            layer = gene.get("layer")
            excluded = gene.get("exclude", True)

            if not excluded and layer in connected_layers:
                # Add layer node
                layer_data = get_node_element(gene)
                element = {"data": layer_data}

                if element not in elements:
                    elements.append(element)

                # Add group node
                group = gene.get("group")
                if group:
                    group_data = {'id': group, 'label': group}
                    element = {"data": group_data}

                    if element not in elements:
                        group_elements.append(element)
                        groups.append(group)

        # Combine group elements with layer elements
        elements = group_elements + elements

        # Build layer connections
        layer_graph = get_layer_graph(run, group_connections=False)

        for layer, edges in layer_graph.items():
            for edge in edges:
                element = {'data': {'source': layer, 'target': edge}, 'classes': f'{layer} {edge}'}

                if element not in elements and layer in connected_layers:
                    elements.append(element)

        # Build group connections
        group_graph = get_group_graph(run)

        for group_source, group_targets in group_graph.items():
            for group_target in group_targets:
                element = {'data': {'source': group_source, 'target': group_target}, 'classes': 'class-connect'}

                if element not in elements and group_source in groups:
                    elements.append(element)

        return elements, groups

    except KeyError as key_error:
        raise KeyError(f"Expected key not found in search space data: {key_error}")

    except TypeError as type_error:
        raise TypeError(f"Unexpected data structure in search space data: {type_error}")

run = "ga_20240108-231402_spoken_languages"

get_layer_graph(run, group_connections=True)
print(get_groups(run))