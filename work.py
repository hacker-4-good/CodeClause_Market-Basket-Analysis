import streamlit as st

st.title('Market Basket Analysis')


import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
pd.set_option('display.max_columns', None)
pd.set_option('display.float_format', lambda x: '%.3f'%x)
import warnings
warnings.filterwarnings("ignore")
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=DeprecationWarning)
df_ = pd.read_excel("CodeClause/online_retail_II.xlsx", sheet_name='Year 2010-2011')
df = df_.copy()
df.dropna(inplace=True)
df_Invoice = pd.DataFrame({"Invoice":[row for row in df['Invoice'].values if "C" not in str(row)]})
df_Invoice.head()
df_Invoice = df_Invoice.drop_duplicates("Invoice")
df = df.merge(df_Invoice, on="Invoice")
def outlier_threshold(dataframe, variable):
    quartile1 = dataframe[variable].quantile(0.01)
    quartile3 = dataframe[variable].quantile(0.99)
    interquantile_range = quartile3 - quartile1
    up_limit = quartile3 + 1.5*interquantile_range
    low_limit = quartile1 - 1.5*interquantile_range
    return low_limit, up_limit

def replace_with_thresholds(dataframe, variable):
    low_limit, up_limit = outlier_threshold(dataframe, variable)
    dataframe.loc[(dataframe[variable]<low_limit), variable] = low_limit
    dataframe.loc[(dataframe[variable]>up_limit), variable] = up_limit
num_cols = [col for col in df.columns if df[col].dtypes in ["int64", "float64"] and "ID" not in col]
for col in num_cols:
    replace_with_thresholds(df, col)
df = df[df['Quantity']>0]
df = df[df['Price']>0]
df_product = df[['Description', 'StockCode']].drop_duplicates()
df_product = df_product.groupby(['Description']).agg({'StockCode':'count'}).reset_index()
df_product.sort_values('StockCode', ascending=False).head()
df_product.rename(columns={'StockCode':'StockCode_Count'}, inplace=True)
df_product = df_product[df_product['StockCode_Count']>1]
df = df[~df['Description'].isin(df_product['Description'])]
df_product = df[['Description', 'StockCode']].drop_duplicates()
df_product = df_product.groupby(['StockCode']).agg({'Description':'count'}).reset_index()
df_product.rename(columns={'Description':'Description_Count'}, inplace=True)
df_product = df_product.sort_values('Description_Count', ascending=False)
df_product = df_product[df_product['Description_Count']>1]
df = df[~df['StockCode'].isin(df_product['StockCode'])]
df = df[~df['StockCode'].str.contains("POST", na=False)]

country = st.selectbox('Select Country', (' ','United Kingdom', 'France', 'Australia', 'Netherland', 'Germany'))
if country == ' ':
    pass
else:
    data = df[df['Country']==country]
    def create_invoice_product_df(dataframe, id=False):
        if id:
            return dataframe.groupby(['Invoice', 'StockCode'])['Quantity'].sum().unstack().fillna(0).applymap(lambda x: 1 if x>0 else 0)
        else:
            return dataframe.groupby(['Invoice', 'Description'])['Quantity'].sum().unstack().fillna(0).applymap(lambda x: 1 if x>0 else 0)
    
    gr_inv_pro_df = create_invoice_product_df(data, id=True)

    def check_id(dataframe, stockcode):
        product_name = dataframe[dataframe['StockCode'] == stockcode]['Description'].unique()[0]
        return product_name

    product_num = st.text_input('Enter the product number')

    if st.button('Submit'):
        st.balloons()
        name = check_id(data, int(product_num))
    
        frequent_itemsets = apriori(gr_inv_pro_df, min_support=0.01, use_colnames=True)
        rules = association_rules(frequent_itemsets, metric='support', min_threshold=0.01)
        sorted_rules = rules.sort_values('lift', ascending=False)
        recommendation_list = []
        for idx, product in enumerate(sorted_rules['antecedents']):
            for j in list(product):
                if j==int(product_num):
                    recommendation_list.append(list(sorted_rules.iloc[idx]['consequents'])[0])
                    recommendation_list = list(dict.fromkeys(recommendation_list))
        list_top6 = recommendation_list[0:6]
        st.write('Product Name: ')
        st.write(str(name))
        st.write('Recommendations: ')
        for ele in list_top6:
            st.write(str(check_id(data, int(ele))))