# PyGrok Debugger Dash by Patrick Dugan. Fall/Winter 2021.
# Props to the following for inspiration: https://grokdebug.herokuapp.com/, https://github.com/cjslack/grok-debugger, https://pypi.org/project/pygrok/, https://plotly.com/dash/, 



import dash, os, json
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, ALL, MATCH
import pandas as pd
from pygrok import Grok
from datetime import datetime as dt


#init empty dataframe
df = pd.DataFrame([{'.':[''],'..':[''],'...':[''],'....':[''],}])

#server 
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets = [dbc.themes.DARKLY, dbc.icons.FONT_AWESOME])
app.title = 'PyGrok Debugger'
server = app.server


#ui
#update this to add github link
navbar = dbc.NavbarSimple(
    children=[],
    brand='PyGrok Debugger',
    color='primary',
    dark=True
)

body = dbc.Container(
    [
        dcc.Store(id='pattern_storage', storage_type='local'),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(html.Div('Registered Patterns: ')),
                dbc.Col(
                    dcc.Dropdown(
                        id='dropdown_pattern',
                        className='mb-1' ,
                        options = [{'label': k, 'value': k} for k in sorted([os.path.splitext(filename)[0] for filename in os.listdir('./assets/patterns')])],
                        style= {
                            'backgroundColor': '#222',
                        }
                    ), 
                    width = 2
                ),
            ], 
            className='g-0',
            align='center'
        ),
        dbc.Row(
            dbc.Textarea(id='registered_pattern', className='mb-3 border-primary', size='md', style ={'color':'#a9a9a9'},
                placeholder='Select a pattern to display here.',
            ),
            align='center',
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(html.Div('Grok Pattern: '), width = {'offset':'start'}),
                dbc.Col(
                        [
                            dcc.Clipboard(
                                target_id='grok_pattern',
                                 title='copy',
                                 className='btn bg-transparent',
                            ),
                            html.Button(html.I(className='far fa-save'),
                                className='btn bg-transparent',
                                id='btn_save',
                            ),
                            html.Button(html.I(className='far fa-folder-open'),
                                className='btn bg-transparent',
                                id='btn_load'
                            ),
                        ],
                        width = { 'size':'auto', 'offset':4, 'order': 'last'} 
                    ),
            ],

        ),
        dbc.Row(
            dbc.Textarea(id='grok_pattern', className='mb-3 border-primary', size='md', style ={'color':'#a9a9a9'},
                value='%{TIMESTAMP_ISO8601:time} %{LOGLEVEL:logLevel} %{GREEDYDATA:logMessage}',
            ),
            align='center',
        ),

        dbc.Row(
            [
                dbc.Col(html.Div('Input'), width = 6, align='start' ),
                dbc.Col(
                    html.Button('Parse', className=('btn bg-transparent mbp-3'), id='btn_parse', n_clicks=0),
                    width = { 'size':1, 'offset':5, 'order': 'last'} 
                )
            ]
        ),
        dbc.Row(
            dbc.Textarea(id='log_input', className='mb-3 border-primary', size='md', 
                style ={'color':'#a9a9a9', 'whiteSpace': 'pre', 'overflowWrap': 'normal', 'overflow': 'auto'},
                value=f"{dt.now().strftime('%Y-%m-%dT%H:%M:%S%z')} DEBUG This is a sample log"
            )
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.Div('Output'), width = 6, align='start'   
                ),
                dbc.Col(
                    [
                        html.Button(html.I(className='far fa-save'), className=('btn bg-transparent mbp-3'), id='btn_download'),
                        dcc.Download(id='download_dataframe_csv'),
                    ],
                    width = { 'size':1, 'offset':5, 'order': 'last'} 
                )
            ]
        ),
        dbc.Row(
            dash_table.DataTable(
                id='output_table',
                columns=[{'name': i, 'id': i} for i in df.columns],
                data=df.to_dict('records'),
                cell_selectable=False,
                style_header={'backgroundColor': '#444', 'color':'#a9a9a9', 'textAlign': 'left', 'border':'1px solid #375a7f'},
                style_cell={'backgroundColor': '#222', 'color':'#a9a9a9', 'textAlign': 'left', 'border':'1px solid #375a7f',},
                style_table={'overflow': 'auto',},
                filter_action='native',
                sort_action='native',
                sort_mode='multi',
                 page_action='native',
                page_current= 0,
                page_size= 10,
                css=[
                        { 'selector': '.previous-page, .first-page, .last-page, .next-page', 'rule': 'background-color: #444; color: #a9a9a9' },
                        { 'selector': '.previous-page :hover, .first-page :hover, .last-page :hover, .next-page :hover .button :hover', 'rule': 'color: #375a7f' }
                    ],
            ),
        )
    ]
)


save_modal = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle('Save Pattern')),
                dbc.ModalBody([
                            dbc.Input(id='pattern_title', placeholder='Pattern Title', style={'color':'#a9a9a9'}),
                ]),
                dbc.ModalFooter(
                    dbc.Button(
                        [
                            html.I(className='far fa-save'),' Save',
                        ],
                        className='ms-auto btn-success mbp-3', id='modal_btn_save',
                        
                    )
                ),
            ],
            id='save_modal',
            is_open=False
        ),
    ]
)


load_modal = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle('Load Pattern')),
                dbc.ModalBody(id='load_modal_table'),
            ],
            id='load_modal',
            is_open=False
        ),
    ]
)

app.layout = html.Div([navbar, body, save_modal, load_modal])


#callbacks

#display selected patterns
@app.callback(
    Output('registered_pattern', 'value'),
    Input('dropdown_pattern', 'value')
)
def update_registered_patterns_text(selected_pattern):
    if selected_pattern is None:
        return 'Select a pattern to display here.'
    with open(f'./assets/patterns/{selected_pattern}') as f:
        data = f.read()
        return data

#update datatable with grokked results
@app.callback(
    Output('output_table','columns'),
    Output('output_table','data'),
    [
        Input('btn_parse', 'n_clicks'),
        State('grok_pattern', 'value'),
        State('log_input', 'value'),
    ]
)
def update_output_table(clicks, pattern, input):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    else:
        triggerBtn = str(ctx.triggered[0]['prop_id'].split('.')[0])
    if triggerBtn == 'btn_parse':
        try:
            grok = Grok(pattern)
            input_list = input.splitlines()
            #remove entries not matching pattern and convert data to pd acceptable format 
            grok_list = [{k:[v] for k,v in grok.match(entry).items()} for entry in input_list if grok.match(entry) is not None]
            df = pd.DataFrame(grok_list)
            columns=[{'name': i, 'id': i} for i in df.columns]
            data=df.to_dict('records')
            return columns, data
        except:
            df = pd.DataFrame([{'Compile Error':['Check your pattern syntax']}])
            columns=[{'name': i, 'id': i} for i in df.columns]
            data=df.to_dict('records')
            return columns, data

#download results
@app.callback(
    Output('download_dataframe_csv', 'data'),
    Input('btn_download', 'n_clicks'),
    State('output_table','columns'),
    State('output_table','data'),
)
def download(clicks, columns, rows):
    ctx = dash.callback_context
    triggerBtn = str(ctx.triggered[0]['prop_id'].split('.')[0])
    if triggerBtn == 'btn_download':
        df_dl = pd.DataFrame(rows)
        for column in list(df_dl.columns):
            df_dl[column] = df_dl[column].astype(str).str.strip("['|']") 
        dl_time = dt.utcnow()
        return dcc.send_data_frame(df_dl.to_csv, f'{dl_time}_cleaned_logs.csv', index=False)



# load saved patterns and update table.
@app.callback(
    Output('load_modal_table', 'children'),
    Input('pattern_storage','data'),
)
def update_modal_table(data):
    table_header = [html.Thead(
        html.Tr([
            html.Td(''),
            html.Td('Title'), 
            html.Td('Pattern'),
            html.Td(''), 
        ])
    )]
    if data:
        table_rows = [html.Tr(
            [
                html.Td(dbc.Button(
                    html.I(className='far fa-folder-open'), 
                    size='sm', n_clicks = 0, id={'type':'row_btn_load', 'index':k},
                    style={'maxWidth':'3em'},
                    className='btn-success'
                )),

                html.Td(f'{k}',style={'max-width':'12em', 'overflow':'hidden', 'whiteSpace': 'nowrap'}), 
                html.Td(f'{v}', style={'max-width':'15em', 'overflow':'hidden', 'whiteSpace': 'nowrap'}),
                html.Td( 
                    dbc.Button([html.I(className='far fa-trash-alt')],
                        className='ms-auto btn-danger', size='sm', n_clicks = 0, id={'type':'row_btn_delete', 'index':k},
                    ),
                style = {'textAlign':'right'}
                ),
            ], id=f'row_{k}'
        ) for k,v in data.items()]
    else: 
        table = dbc.Table(table_header)
        return table

    table_body=[html.Tbody(table_rows)]
    table = dbc.Table(table_header+table_body)
    return table



#open/close load modal
@app.callback(
    Output('load_modal', 'is_open'),
    [
        Input('btn_load', 'n_clicks'), 
        Input({'type':'row_btn_delete', 'index':ALL}, 'n_clicks'), 
        Input({'type':'row_btn_load', 'index':ALL}, 'n_clicks')
    ],
    State('load_modal', 'is_open'),
)
def toggle_modal(n1, n2, n3, is_open):
    ctx = dash.callback_context
    if ctx.triggered[0]['value'] is None:
        return dash.no_update
    else:
        triggerBtn = str(ctx.triggered[0]['prop_id'].split('.')[0])
        if triggerBtn == 'btn_load':
            return not is_open
        else:
            triggerBtn = json.loads(triggerBtn)
            if triggerBtn['type']=='row_btn_delete':
                return False
            if triggerBtn['type']=='row_btn_load':
                return False
        


#open /close save modal
@app.callback(
    Output('save_modal', 'is_open'),
    [Input('btn_save', 'n_clicks'), Input('modal_btn_save', 'n_clicks')], 
    State('save_modal', 'is_open'),
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


#handle patterns in browser storage
@app.callback(
    Output('pattern_storage', 'data'),
        [
            Input('modal_btn_save', 'n_clicks'), 
            Input({'type': 'row_btn_delete', 'index': ALL}, 'n_clicks')
        ],
        [
            State('pattern_title', 'value'),
            State('grok_pattern', 'value'),
            State('pattern_storage', 'data'),
        ]
)
def save_pattern_data(save_click, delete_click, title, pattern, stored_patterns):
    ctx = dash.callback_context
    triggerBtn = str(ctx.triggered[0]['prop_id'].split('.')[0])   
    if ctx.triggered[0]['value'] is None or ctx.triggered[0]['value'] == 0:
        return dash.no_update
    if triggerBtn == 'modal_btn_save':
        if stored_patterns is None:
            stored_patterns={}
        stored_patterns[title]=pattern
        return stored_patterns
    else: 
        triggerBtn = json.loads(triggerBtn)
        if triggerBtn['type']=='row_btn_delete':
            del stored_patterns[triggerBtn['index']]
            return stored_patterns

#clear title field after save
@app.callback(
    Output('pattern_title', 'value'),
    Input('modal_btn_save', 'n_clicks')
)
def clear_title_field(trigger):
    if trigger is None:
        return dash.no_update
    else: return ''

@app.callback(
    Output('grok_pattern', 'value'),
    Input({'type':'row_btn_load', 'index':ALL}, 'n_clicks'),
    State('pattern_storage', 'data')
)
def load_grok_pattern(trigger, stored_patterns):
    ctx = dash.callback_context
    if ctx.triggered[0]['value'] is None or ctx.triggered[0]['value'] == 0:
        return dash.no_update
    else:
        triggerBtn = json.loads(str(ctx.triggered[0]['prop_id'].split('.')[0]))
        if triggerBtn['type']=='row_btn_load':
            return stored_patterns[triggerBtn['index']]



if __name__ == '__main__':
    app.run_server()