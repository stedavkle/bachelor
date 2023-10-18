import PySimpleGUI as sg
import augmentor
import SEM_API_CUSTOM
import os
import nanocontrol
import time

sem = None
aug = None
con = None

rot_keys = ['r0', 'r45', 'r90', 'r135', 'r180', 'r225', 'r270', 'r315']
detector_keys = ['InLens', 'SE2', 'EBIC']
scanrate_keys = ['sr1', 'sr2', 'sr3', 'sr4', 'sr5', 'sr6', 'sr7', 'sr8', 'sr9', 'sr10', 'sr11', 'sr12', 'sr13', 'sr14', 'sr15']
wd_deviations = ['0.003', '0.004', '0.005', '0.006', '0.007']

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
    [sg.Button('Grab Masks', disabled=True), sg.Button('Grab Images', disabled=True), sg.Button('Cancel')]
]

nc_control = [
    [sg.Text('Here you can control the nanocontrol')],
    [sg.Button('Connect', key='nc_connect'), sg.Button('Disconnect', disabled=True, key='nc_disconnect')],
    [sg.Checkbox('Tip 1', key='tip1', disabled=True), sg.Checkbox('Tip 2', key='tip2', disabled=True), sg.Checkbox('Tip 3', key='tip3', disabled=True), sg.Checkbox('Tip 4', key='tip4', disabled=True), sg.Checkbox('Tip 5', key='tip5', disabled=True), sg.Checkbox('Tip 6', key='tip6', disabled=True), sg.Checkbox('Tip 7', key='tip7', disabled=True), sg.Checkbox('Tip 8', key='tip8', disabled=True), sg.Checkbox('Substage', key='tip31', disabled=True)],
    [sg.Button('Assign patterns', disabled=True, key='nc_pattern')],
    [sg.Text('Retract length:'), sg.InputText(key='nc_ret_len', size=(10, 1)), sg.Combo(['um', 'nm'], default_value='um', key='nc_ret_unit')],
    [sg.Button('Retract', disabled=True, key='nc_retract')],
]

runner = [
    [sg.Text('Here you can run the whole process')],
    [sg.Button('Run')]
]

layout = [
    [sg.TabGroup([[ sg.Tab('SEM Control', [[sg.Column(sem_control), sg.VSeparator(), sg.Column(sem_parameter)]]),
                    sg.Tab('Augmentation Control', aug_control, disabled=False),
                    sg.Tab('Nanocontrol', nc_control),
                    sg.Tab('Runner', runner)
                ]])],
    [sg.Multiline(size=(50, 20), key='log', autoscroll=True)],
    [sg.Button('Exit'), sg.Button('Test')],
]

window = sg.Window('My Program', layout)

event, values = window.read(timeout=100)

window['r0'].update(True)
window['r135'].update(True)
window['InLens'].update(True)
window['SE2'].update(True)
window['sr2'].update(True)
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
        window.start_thread(aug.grabMasks, "grab")
    if event == 'Grab Images':
        window['log'].print('Grabbing images')
        window['Grab Masks'].update(disabled=True)
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


    if event == 'nc_connect':
        window['log'].print('Nanocontrols connected')
        if con is None:
            con = nanocontrol.controller()
            for nc in con.ncs.keys():
                window['log'].print(nc)
                window["tip"+str(nc)].update(True)
        window['nc_connect'].update(disabled=True)
        window['nc_disconnect'].update(disabled=False)
        window['nc_pattern'].update(disabled=False)
    if event == 'nc_disconnect':
        window['log'].print('Nanocontrols disconnected')
        for nc in con.ncs.keys():
            window["tip"+str(nc)].update(False)
        con = None
        window['nc_connect'].update(disabled=False)
        window['nc_disconnect'].update(disabled=True)
    if event == 'nc_pattern':
        nc_pt = con.assignPattern()
        window['log'].print('Pattern assigned')
        window['log'].print(nc_pt)
        window['nc_retract'].update(disabled=False)
    if event == 'nc_retract':
        ret = con.retractStep()
        if ret == 0:
            window['log'].print('Retraction complete')
            window['nc_retract'].update(disabled=True)
        else:
            window['log'].print('Retracted')

    ## runner
    if event == 'Run':
        window['Run'].update(disabled=True)
        running = True
        while running:
            window['log'].print('Grabbing masks')
            window.start_thread(aug.grabMasks, "nix")

            while aug.running:
                time.sleep(3)
                print('waiting')

            window['log'].print('Grabbing images')
            window.start_thread(aug.grabImages, "nix")

            while aug.running:
                time.sleep(3)
                print('waiting')

            aug.iteration += 1
            window['log'].print('Grabbing done')
            ret = con.retractStep()
            if ret == 0:
                running = False
                window['Run'].update(disabled=False)
                window['log'].print('Iteration done, please relocate tips.')






    
    if event == 'Test':
        print(values)
window.close()