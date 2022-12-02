import collections
import pandas as pd
import json

def detect_attacks(timestamp, audit_file='./audit2.json'):

    try:
        data = pd.read_json(audit_file, lines=True)
        json_struct = json.loads(data.to_json(orient="records"))  
        df = pd.json_normalize(json_struct)
        df = df.explode('sourceIPs')
    except:
        print("Exception")
        pass
    threshold = 1

    def topNCheck(col):
        if timestamp == 0:
            prev = df[col].value_counts(10)
        
        cur = df[col].value_counts(10)
        exclusive_items = [x for x in set(cur) if x not in set(prev)]

        if not timestamp % 5:
                prev = cur
        if len(exclusive_items):
            return True, exclusive_items
        return False, []
    
    def authorization_decision():
        try:
            df2 = df.loc[(df['annotations.authorization.k8s.io/decision'] == 'forbid')]
            df3 = df2.groupby(['user.username'])['user.username'].count().sort_values(ascending=False).head(10)
            result = df3.to_string
            return result
        except:
            return "Series([], )"

    def associations(col, vals, associated_col):
        result = {}
        try:
            for val in vals:
                df2 = df.loc[df[col] == val, associated_col]
                result[val] = df2.unique()
            return result
        except:
            return result
    
    def execution_phase():
        try:
            df2 = df.loc[(df['annotations.authorization.k8s.io/decision'] == 'forbid') & (df['objectRef.subresource'] == 'exec')]
            df3 = df2.groupby(['user.username', 'objectRef.resource', 'objectRef.subresource'])['user.username'].count().sort_values(ascending=False).head(10)
            result = df3[df3 > threshold].to_string()
            return result
        except:
            return "Series([], )"
    
    def persistence():
        try:
            df2 = df.loc[(df['annotations.authorization.k8s.io/decision'] == 'forbid') & (df['objectRef.resource'] == 'cronjobs')]
            df3 = df2.groupby(['user.username', 'objectRef.resource', 'sourceIPs'])['user.username'].count().sort_values(ascending=False).head(10)
            result = df3[df3 > threshold].to_string()
            return result
        except:
            return "Series([], )"

    # verb can be list, watch, delete
    def defensive_evasion(verb='list'):
        try:
            df2 = df.loc[(df['verb'] == verb) & (df['objectRef.resource'] == 'events')]
            df3 = df2.groupby(['verb', 'user.username', 'objectRef.resource', 'sourceIPs'])['user.username'].count().sort_values(ascending=False).head(10)
            result = df3[df3 > threshold].to_string()
            return result
        except:
            return "Series([], )"
    
    def discovery_learn():
        try:
            df2 = df.loc[(df['responseStatus.code'] == 404) & (df['objectRef.resource'] == 'networkpolicies')]
            df3 = df2.groupby(['verb', 'user.username', 'objectRef.resource'])['user.username'].count().sort_values(ascending=False).head(10)

            result = df3[df3 > threshold].to_string()
            return result
        except:
            return "Series([], )"

    def discovery_modify():
        try:
            df2 = df.loc[(df['objectRef.resource'] == 'networkpolicies')]
            df3 = df2.groupby(['verb', 'user.username'])['user.username'].count().sort_values(ascending=False).head(10)

            result = df3[df3 > threshold].to_string()
            return result
        except:
            return "Series([], )"
    
    def lateral_movement():
        try:
            df2 = df.loc[(df['objectRef.resource'] == 'secrets') & (df['verb'] == 'list') | (df['verb'] == 'watch') | (df['verb'] == 'get') & (df['annotations.authorization.k8s.io/decision'] == 'forbid')]
            df3 = df2.groupby(['verb', 'user.username'])['user.username'].count().sort_values(ascending=False).head(10)
            if len(df3[df3 > threshold]) > 0:
                print(df3[df3 > threshold])
            result = df3[df3 > threshold].to_string()
            return result
        except:
            return "Series([], )"

    def impact_pre():
        try:
            df2 = df.loc[(df['objectRef.resource'] == 'configmaps') & (df['verb'] == 'list') | (df['verb'] == 'watch') | (df['verb'] == 'get')]
            df3 = df2.groupby(['verb', 'user.username'])['user.username'].count().sort_values(ascending=False).head(10)

            result = df3[df3 > threshold].to_string()
            return result
        except:
            return "Series([], )"

    def impact_post():
        try:
            df2 = df.loc[(df['objectRef.resource'] == 'configmaps') & (df['verb'] == 'delete') | (df['verb'] == 'update')]
            df3 = df2.groupby(['verb', 'user.username'])['user.username'].count().sort_values(ascending=False).head(10)

            result = df3[df3 > threshold].to_string()
            return result
        except:
            return "Series([], )"
    
    # # top N entity detections
    # topNCheck('userAgent')
    # topNCheck('sourceIPs')
    # topNCheck('user.username')
    # topNCheck('responseStatus.code')

    # # associated users
    # associations('userAgent', ['Go-http-client/2.0'], 'user.username')
    # authorization_decision()

    # threat matrix attacks
    # todo - priviledge escalation, credential access
    attacks = {}
    types = {0: 'execution', 1: 'persistence', 2: 'defensive_evasion', 3: 'discovery_learn', 4: 'discovery_modify', 5: 'lateral_movement', 6: 'impact_pre', 7: 'impact_post'}
    results = [execution_phase(), persistence(), defensive_evasion(), discovery_learn(), discovery_modify(), lateral_movement(), impact_pre(), impact_post()]

    for i in range(len(results)):
        if results[i] !=  "Series([], )" and len(results[i]):
            attacks[types[i]] = results[i]
    
    return attacks