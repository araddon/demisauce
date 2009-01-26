
class xmlrpcnode(object): pass
    
def parse_result(xml_list):
    """
    Recursive call to process this dict
    """
    result = []
    if type(xml_list) is dict:
        xml_list = [xml_list]
    for row in xml_list:
        if type(row) is not dict and type(row) is not list:
            result.append(row)
        else:
            o = xmlrpcnode()
            result.append(o)
            for key in row.keys():
                if type(row[key]) == list:
                    o.__dict__[key] = parse_result(row[key])
                else:
                    o.__dict__[key] = row[key]
    
    return result


if __name__=='__main__':
    xml_result = [{
        'wp_author': 'admin', 
        'userid': '1', 
        'excerpt': '', 
        'wp_page_parent_id': '0', 
        'mt_allow_comments': 1, 
        'text_more': '', 
        'custom_fields': [
            {'value': 'my fake value', 'id': '7', 'key': 'dskey'}, 
            {'value': '1', 'id': '2', 'key': '_edit_last'}, 
            {'value': '1220232747', 'id': '1', 'key': '_edit_lock'}
        ], 
        'wp_author_id': '1', 
        'title': 'About', 
        'wp_password': '', 
        'wp_page_parent_title': '', 
        'page_id': '2', 
        'wp_slug': 'about', 
        'wp_page_order': '0', 
        'permaLink': 'http://192.168.125.133/blog/?page_id=2', 
        'description': 'Demisauce is a good system for doing all kinds of things.', 
        'dateCreated': '', 
        'wp_author_display_name': 'admin', 
        'link': 'http://192.168.125.133/blog/?page_id=2', 
        'page_status': 'publish', 
        'categories': ['Uncategorized'], 
        'wp_page_template': 'default', 
        'mt_allow_pings': 1, 
        'date_created_gmt': ''}]

    o = parse_result(xml_result)[0]
    assert o.wp_author == 'admin'
    assert o.wp_author_id == '1'
    assert o.categories[0] == 'Uncategorized'