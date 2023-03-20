import PySimpleGUI as sg
import augmentor
import SEM_API_CUSTOM
import os

sem = None
aug = None

rot_keys = ['r0', 'r45', 'r90', 'r135', 'r180', 'r225', 'r270', 'r315']
detector_keys = ['InLens', 'SE2', 'EBIC']
scanrate_keys = ['sr1', 'sr2', 'sr3', 'sr4', 'sr5', 'sr6', 'sr7', 'sr8', 'sr9', 'sr10', 'sr11', 'sr12', 'sr13', 'sr14', 'sr15']
wd_deviations = ['0.3', '0.4', '0.5', '0.6', '0.7']

sg.theme('DarkBrown4')   # Add a touch of color

sem_control = [
    [sg.Text('Here you can connect to the SEM and control it')],
    [sg.Button('Connect'), sg.Button('Disconnect', disabled=True)],
    [sg.Button('Save', disabled=True), sg.Button('Restore', disabled=True)]
]
sem_parameter = [
    [sg.Text('Mag:'), sg.InputText(key='mag', size=(10, 1))],
    [sg.Text('WD:'), sg.InputText(key='wd', size=(10, 1))],
    [sg.Text('Rot:'), sg.InputText(key='rot', size=(10, 1))],
    [sg.Text('Detector:'), sg.InputText(key='detector', size=(10, 1))],
    [sg.Text('Scanrate:'), sg.InputText(key='scanrate', size=(10, 1))]
]

aug_control = [
    [sg.Text('Here you can control the augmentation')],
    [sg.Text('Dataset Path:'), sg.Input(key='path', default_text="D:/datasets/automated/", size=(50, 1))],
    [sg.Text('Magnifications:'), sg.Input(key='mags', default_text="1000,5000,10000", size=(50, 1))],
    [sg.Text('Rotations:')] + [sg.Checkbox(key[1:], key=key) for key in rot_keys],
    [sg.Text('Detectors:')] + [sg.Checkbox(key, key=key) for key in detector_keys],
    [sg.Text('Scanrates:')] + [sg.Checkbox(key[2:], key=key) for key in scanrate_keys],
    [sg.Text('WD Deviation %:'), sg.Combo(wd_deviations, default_value='0.5', key='wd_deviation')],
    [sg.Button('Augment')],
    [sg.Button('Grab Masks',disabled=True), sg.Button('Grab Images', disabled=True), sg.Button('Cancel')]
]


layout = [
    [sg.TabGroup([[sg.Tab('SEM Control', [[sg.Column(sem_control), sg.VSeparator(), sg.Column(sem_parameter)]]), sg.Tab('Augmentation Control', aug_control, disabled=True)]])],
    [sg.Multiline(size=(50, 20), key='log', autoscroll=True)],
    [sg.Button('Exit'), sg.Button('Test')]
]

window = sg.Window('My Program', layout)

window['r0'].update(True)
window['r90'].update(True)
window['InLens'].update(True)
window['SE2'].update(True)
window['sr3'].update(True)
window['sr6'].update(True)

while True:
    event, values = window.read(timeout=100)
    if event in (sg.WIN_CLOSED, 'Exit'):
      break
    
    # SEM Control
    if event == 'Connect':
        if sem is None:
            sem = SEM_API_CUSTOM.SEM_API_CUSTOM()
        try:
            sem.openConnection()
            window['log'].print('Connected to SEM')
            window['Connect'].update(disabled=True)
            window['Restore'].update(disabled=False)
            window['Save'].update(disabled=False)
            window['Disconnect'].update(disabled=False)
            window['Exit'].update(disabled=True)
        except SEM_API_CUSTOM.API_ERROR as e:
            window['log'].print(e.error_text)
    if event == 'Disconnect':
        sem.closeConnection()
        window['log'].print('Disconnected from SEM')
        window['Connect'].update(disabled=False)
        window['Restore'].update(disabled=True)
        window['Save'].update(disabled=True)
        window['Disconnect'].update(disabled=True)
        window['Exit'].update(disabled=False)
    if event == 'Save':
        params = sem.getInitialParameters()
        print(params)
        window['log'].print('Initial parameters saved')
        window['mag'].update(params[0])
        window['wd'].update(params[4])
        window['rot'].update(params[1])
        window['detector'].update(params[2])
        window['scanrate'].update(params[3])
        window['Save'].update(disabled=True)
        window['Augmentation Control'].update(disabled=False)
    if event == 'Restore':
        sem.restoreInitialParameters()
        window['log'].print('Initial parameters restored')
        window['Save'].update(disabled=False)

    # Augmentation Control
    if event == 'Augment':
        if aug is None:
            aug = augmentor.augmentor(sem)
        window['path'].update(disabled=True)
        window['Augment'].update(disabled=True)
        [window[key].update(disabled=True) for key in rot_keys + detector_keys + scanrate_keys]

        mag = values['mags'].split(',')
        rot = [key[1:] for key in rot_keys if values[key]]
        detector = [key for key in detector_keys if values[key]]
        scanrate = [key[2:] for key in scanrate_keys if values[key]]
        if len(mag) == 0 or len(rot) == 0 or len(detector) == 0 or len(scanrate) == 0:
            window['log'].print('Please select at least one value for each parameter')
            continue
        else:
            mask_count, image_count = aug.setParameters(os.path.join(values['path']), values['wd_deviation'], mag, rot, detector, scanrate)
            window['log'].print('Augmentation done')
            window['log'].print('Masks: ' + str(mask_count), ', Images: ' + str(image_count))
            window['Grab Masks'].update(disabled=False)
            window['Grab Images'].update(disabled=False)
    if event == 'Grab Masks':
        window['log'].print('Grabbing masks')
        window['Grab Images'].update(disabled=True)
        aug.running = True
        window.start_thread(aug.grabMasks, "grab")
    if event == 'Grab Images':
        window['log'].print('Grabbing images')
        window['Grab Masks'].update(disabled=True)
        aug.running = True
        window.start_thread(aug.grabImages, "grab")
    if event == 'Cancel':
        aug.running = False
        window['Grab Masks'].update(disabled=False)
        window['Grab Images'].update(disabled=False)
        window['Augment'].update(disabled=False)
        window['log'].print('Grabbing canceled')
        window['path'].update(disabled=False)
        [window[key].update(disabled=False) for key in rot_keys + detector_keys + scanrate_keys]

    if event == 'grab':
        window['Grab Masks'].update(disabled=False)
        window['Grab Images'].update(disabled=False)
        window['log'].print('Grabbing done')
    if event == 'Test':
        print(values)
window.close()