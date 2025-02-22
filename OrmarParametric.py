# Assuming you have not changed the general structure of the template no modification is needed in this file.
# import traceback
from . import commands
from .lib import fusionAddInUtils as futil
# import adsk.core
# import adsk.fusion


# # Command handler for when the button is clicked
# class MyCommandHandler(adsk.core.CommandCreatedEventHandler):
#     def __init__(self):
#         super().__init__()
#     def notify(self, args):
#         try:
#             app = adsk.core.Application.get()
#             ui = app.userInterface
#             # Replace this with your custom script logic
#             ui.messageBox("Hello! Your custom script is running.")
#         except:
#             ui = adsk.core.Application.get().userInterface
#             ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            

# def create_toolbar_button():
#     app = adsk.core.Application.get()
#     ui = app.userInterface

#     # Get the existing toolbar panel or create a new one
#     toolbar_panel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
#     if not toolbar_panel:
#         toolbar_panel = ui.allToolbarPanels.add('SolidScriptsAddinsPanel', 'Add-Ins', 'SelectPanel', False)

#     # Create the command definition
#     cmd_id = 'OrmarParametric'
#     cmd_name = 'Ormar Parametric'
#     cmd_desc = 'Konfiguracija Ormara'
#     cmd_def = ui.commandDefinitions.itemById(cmd_id)
#     if cmd_def:
#             cmd_def.deleteMe()  # Clean up if it already exists
#     cmd_def = ui.commandDefinitions.addButtonDefinition(cmd_id, cmd_name, cmd_desc)

#     # Add the command to the toolbar panel
#     toolbar_panel.controls.addCommand(cmd_def)

#     on_command_created = MyCommandHandler()
#     # Connect the command to the run function
#     cmd_def.commandCreated.add(on_command_created)

# def run_command_created(args: adsk.core.CommandCreatedEventArgs):
#     cmd = args.command
#     cmd.execute.add(run_command_execute)

# def run_command_execute(args: adsk.core.CommandEventArgs):
#     run(None)

# create_toolbar_button()

# def show_options_dialog():
#     app = adsk.core.Application.get()
#     ui = app.userInterface

#     dialog = ui.createDialog()
#     dialog.title = 'Options'

#     gornje_ukrute = dialog.addCheckBox('Gornje Ukrute', True)
#     gornja_ploca = dialog.addCheckBox('Gornja Ploca', True)
#     skrivena_ledja = dialog.addCheckBox('Skrivena Ledja', False)

#     if dialog.show() == adsk.core.DialogResults.DialogOK:
#         options = {
#             'gornje_ukrute': gornje_ukrute.value,
#             'gornja_ploca': gornja_ploca.value,
#             'skrivena_ledja': skrivena_ledja.value
#         }
#         return options
#     else:
#         return None

def run(context):
    try:
        # options = show_options_dialog()
        # if options:
        #     # Process the options here
        #     print(options)

        # This will run the start function in each of your commands as defined in commands/__init__.py
        commands.start()

    except:
        futil.handle_error('run')


def stop(context):
    try:
        # Remove all of the event handlers your app has created
        futil.clear_handlers()

        # This will run the start function in each of your commands as defined in commands/__init__.py
        commands.stop()

    except:
        futil.handle_error('stop')