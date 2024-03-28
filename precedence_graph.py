init_state_1x1 = {'A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'E1', 'E2'}
path_1x1 = 'data/dag_1-1.xlsx'

init_state_2x2 = {'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'B1', 'B2', 'B3', 'E1', 'E2', 'E3', 'E4'}
path_2x2 = 'data/dag_2-2.xlsx'

init_state_2x3 = {'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'B1', 'B2', 'B3', 'B4', 'E1', 'E2', 'E3', 'E4', 'E5', 'E6'}
path_2x3 = 'data/dag_2-3.xlsx'

init_state_2x4 = {'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'B1', 'B2', 'B3', 'B4', 'B5', 'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8'}
path_2x4 = 'data/dag_2-4.xlsx'

init_state_2x6 = {'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12', 'A13', 'A14',
              'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7',
              'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10', 'E11', 'E12'
              }
path_2x6 = 'data/dag_2-6.xlsx'

init_state_2x8 = {
    'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12', 'A13', 'A14', 'A15', 'A16',
    'A17',
    'A18',
    'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9',
    'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10', 'E11', 'E12', 'E13', 'E14', 'E15', 'E16',
}
path_2x8 = 'data/dag_2-8.xlsx'

init_state_2x10 = {
    'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12', 'A13', 'A14', 'A15', 'A16',
    'A17',
    'A18', 'A19', 'A20', 'A21', 'A22',
    'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11',
    'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10', 'E11', 'E12', 'E13', 'E14', 'E15', 'E16',
    'E17',
    'E18', 'E19', 'E20'
}
path_2x10 = 'data/dag_2-10.xlsx'

init_state_2x2_no_baseplate = {'D1', 'D2', 'D3', 'E1', 'E2', 'E3', 'E4'}
path_2x2_no_baseplate = 'data/dag_2-2-no-baseplate.xlsx'

precedence_graph = {
    '1x1': [init_state_1x1, path_1x1],
    '2x2': [init_state_2x2, path_2x2],
    '2x3': [init_state_2x3, path_2x3],
    '2x4': [init_state_2x4, path_2x4],
    '2x6': [init_state_2x6, path_2x6],
    '2x8': [init_state_2x8, path_2x8],
    '2x10': [init_state_2x10, path_2x10],
    '2x2_no_baseplate': [init_state_2x2_no_baseplate, path_2x2_no_baseplate]
}
