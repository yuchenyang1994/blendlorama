extends Node

@onready var extension_api: Node
var sync_panel = preload("res://src/Extensions/BlenderPixelorama/BlenderLoramaPanel.tscn")
var panel

func _enter_tree() -> void:
	extension_api = get_node_or_null("/root/ExtensionsApi")  # Accessing the Api

	# add a test panel as a tab  (this is an example) the tab is located at the same
	# place as the (Tools tab) by default
	panel = sync_panel.instantiate()
	extension_api.panel.add_node_as_tab(panel)

func _exit_tree() -> void:  # Extension is being uninstalled or disabled
	extension_api.panel.remove_node_from_tab(panel)
