name='tavily_tavily_search' 
title=None 
description='Search the web for current information on any topic. Use for news, facts, or data beyond your knowledge cutoff. Returns snippets and source URLs.' 
inputSchema={
  'additionalProperties': False, 
  'properties': {
    'query': {'description': 'Search query', 'type': 'string'}, 
    'max_results': {'default': 5, 'description': 'The maximum number of search results to return', 'type': 'integer'}, 
    'search_depth': {'default': 'basic', 'description': "The depth of the search. 'basic' for generic results, 'advanced' for more thorough search, 'fast' for optimized low latency with high relevance, 'ultra-fast' for prioritizing latency above all else", 'enum': ['basic', 'advanced', 'fast', 'ultra-fast'], 'type': 'string'}, 
    'topic': {'const': 'general', 'default': 'general', 'description': 'The category of the search. This will determine which of our agents will be used for the search', 'type': 'string'}, 
    'time_range': {'anyOf': [{'enum': ['day', 'week', 'month', 'year'], 'type': 'string'}, {'type': 'null'}], 'default': None, 'description': 'The time range back from the current date to include in the search results'}, 
    'include_images': {'default': False, 'description': 'Include a list of query-related images in the response', 'type': 'boolean'}, 'include_image_descriptions': {'default': False, 'description': 'Include a list of query-related images and their descriptions in the response', 'type': 'boolean'}, 
    'include_raw_content': {'default': False, 'description': 'Include the cleaned and parsed HTML content of each search result', 'type': 'boolean'}, 
    'include_domains': {'default': [], 'description': 'A list of domains to specifically include in the search results, if the user asks to search on specific sites set this to the domain of the site', 'items': {'type': 'string'}, 'type': 'array'}, 
    'exclude_domains': {'default': [], 'description': 'List of domains to specifically exclude, if the user asks to exclude a domain set this to the domain of the site', 'items': {'type': 'string'}, 'type': 'array'}, 
    'country': {'default': '', 'description': "Boost search results from a specific country. Must be a full country name (e.g., 'United States', 'Japan', 'Germany'). ISO country codes (e.g., 'us', 'jp') are not supported. Available only if topic is general. See https://docs.tavily.com/documentation/api-reference/search for the full list of supported countries.", 'type': 'string'}, 
    'include_favicon': {'default': False, 'description': 'Whether to include the favicon URL for each result', 'type': 'boolean'}, 
    'start_date': {'default': '', 'description': 'Will return all results after the specified start date. Required to be written in the format YYYY-MM-DD.', 'type': 'string'}, 
    'end_date': {'default': '', 'description': 'Will return all results before the specified end date. Required to be written in the format YYYY-MM-DD', 'type': 'string'}, 
    'exact_match': {'anyOf': [{'type': 'boolean'}, {'type': 'null'}], 'default': None, 'description': 'Only return results containing the exact phrase(s) in quotes in your query'}}, 'required': ['query'], 'type': 'object'} 
outputSchema={'additionalProperties': True, 'type': 'object'} 
icons=None 
annotations=ToolAnnotations(title=None, readOnlyHint=True, destructiveHint=False, idempotentHint=False, openWorldHint=True) 
meta={'fastmcp': {'tags': []}} 
execution=None