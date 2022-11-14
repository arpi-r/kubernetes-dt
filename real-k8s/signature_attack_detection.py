import collections
import pandas as pd
import json

def detect_attacks(timestamp, audit_file='./audit.json'):

    data = pd.read_json(audit_file, lines=True)
    json_struct = json.loads(data.to_json(orient="records"))    
    df = pd.json_normalize(json_struct)
    df = df.explode('sourceIPs')

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
        df2 = df.loc[(df['annotations.authorization.k8s.io/decision'] == 'forbid')]
        df3 = df2.groupby(['user.username'])['user.username'].count().sort_values(ascending=False).head(10)
        result = df3.to_list
        return result

    def associations(col, vals, associated_col):
        result = {}
        for val in vals:
            df2 = df.loc[df[col] == val, associated_col]
            result[val] = df2.unique()
        return result
    
    def execution_phase():
        df2 = df.loc[(df['annotations.authorization.k8s.io/decision'] == 'forbid') & (df['objectRef.subresource'] == 'exec')]
        df3 = df2.groupby(['user.username', 'objectRef.resource', 'objectRef.subresource'])['user.username'].count().sort_values(ascending=False).head(10)
        result = df3.to_list
        return result
    
    def persistence():
        df2 = df.loc[(df['annotations.authorization.k8s.io/decision'] == 'forbid') & (df['objectRef.resource'] == 'cronjobs')]
        df3 = df2.groupby(['user.username', 'objectRef.resource', 'sourceIPs'])['user.username'].count().sort_values(ascending=False).head(10)
        result = df3.to_list
        return result

    # verb can be list, watch, delete
    def defensive_evasion(verb='list'):
        df2 = df.loc[(df['verb'] == verb) & (df['objectRef.resource'] == 'events')]
        df3 = df2.groupby(['verb', 'user.username', 'objectRef.resource', 'sourceIPs'])['user.username'].count().sort_values(ascending=False).head(10)
        result = df3.to_list
        return result
    
    def discovery():
        df2 = df.loc[(df['responseStatus.code'] == 404) & (df['objectRef.resource'] == 'networkpolicies')]
        df3 = df2.groupby(['verb', 'user.username', 'objectRef.resource'])['user.username'].count().sort_values(ascending=False).head(10)

        df4 = df.loc[(df['objectRef.resource'] == 'networkpolicies')]
        df5 = df4.groupby(['verb', 'user.username'])['user.username'].count().sort_values(ascending=False).head(10)

        result = (df3 + df5).unique()
        return result
    
    def lateral_movement():
        df2 = df.loc[(df['objectRef.resource'] == 'secrets') & (df['verb'] == 'list' | df['verb'] == 'watch' | df['verb'] == 'get') & (df['annotations.authorization.k8s.io/decision'] == 'forbid')]
        df3 = df2.groupby(['verb', 'user.username'])['user.username'].count().sort_values(ascending=False).head(10)

        result = df3.to_list
        return result

    def impact_pre():
        df2 = df.loc[(df['objectRef.resource'] == 'configmaps') & (df['verb'] == 'list' | df['verb'] == 'watch' | df['verb'] == 'get')]
        df3 = df2.groupby(['verb', 'user.username'])['user.username'].count().sort_values(ascending=False).head(10)

        result = df3.to_list
        return result

    def impact_post():
        df2 = df.loc[(df['objectRef.resource'] == 'configmaps') & (df['verb'] == 'delete' | df['verb'] == 'update')]
        df3 = df2.groupby(['verb', 'user.username'])['user.username'].count().sort_values(ascending=False).head(10)

        result = df3.to_list
        return result
    
    # top N entity detections
    topNCheck('userAgent')
    topNCheck('sourceIPs')
    topNCheck('user.username')
    topNCheck('responseStatus.code')

    # associated users
    associations('userAgent', ['Go-http-client/2.0'], 'user.username')
    authorization_decision()

    # threat matrix attacks
    # todo - priviledge escalation, credential access
    attacks = {}
    types = {0: 'execution', 1: 'persistence', 2: 'defensive_evasion', 3: 'discovery', 4: 'lateral_movement', 5: 'impact_pre', 6: 'impact_post'}
    results = [execution_phase(), persistence(), defensive_evasion(), discovery(), lateral_movement(), impact_pre(), impact_post()]

    for i in len(results):
        if len(results[i]):
            attacks[types[i]] = results[i]
    
    return attacks