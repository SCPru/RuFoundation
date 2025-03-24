def validate_mime(mime1: str, mime2: str):
    type1, subtype1 = mime1.split('/')
    type2, subtype2 = mime2.split('/')

    if type1 == subtype1 == '*' or \
       type1 == type2 and \
      (subtype1 in ('*', subtype2) or subtype2 in ('*', subtype1)):
        return True
    
    return False