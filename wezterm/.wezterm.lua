local wezterm = require("wezterm")
local config = wezterm.config_builder()

-- appearance
config.font = wezterm.font 'JetBrainsMonoNL-Regular'
config.font_size = 11

-- Window appearance
config.window_decorations = "RESIZE"
config.window_background_opacity = 0.93
config.window_padding = {
	left = "1cell",
	right = "1cell",
	top = "0.0cell",
	bottom = "0.5cell",
}
config.initial_rows = 42
config.initial_cols = 124

-- Colorscheme
config.color_scheme = 'Tokyo Night (Gogh)'
config.colors = {
	foreground = "#CBE0F0",
	background = "#011423",
	cursor_bg = "#47FF9C",
	cursor_border = "#47FF9C",
	cursor_fg = "#011423",
	selection_bg = "#033259",
	selection_fg = "#CBE0F0",
	ansi = { "#214969", "#E52E2E", "#44FFB1", "#FFE073", "#0FC5ED", "#a277ff", "#24EAF7", "#24EAF7" },
	brights = { "#214969", "#E52E2E", "#44FFB1", "#FFE073", "#A277FF", "#a277ff", "#24EAF7", "#24EAF7" },
}

-- Dim inactive panes
config.inactive_pane_hsb = {
	saturation = 0.24,
	brightness = 0.5,
}



-- tab bar & status
config.enable_tab_bar = false
config.use_fancy_tab_bar = true
config.tab_bar_at_bottom = false

-- Status bar configuration
config.status_update_interval = 1000
wezterm.on("update-status", function(window, pane)
	local basename = function(s)
		return string.gsub(s, "(.*[/\\])(.*)", "%2")
	end

	-- Current working directory
	local cwd = pane:get_current_working_dir()
	if cwd then
		if type(cwd) == "userdata" then
			cwd = basename(cwd.file_path)
		else
			cwd = basename(cwd)
		end
	else
		cwd = ""
	end

	-- Current command
	local cmd = pane:get_foreground_process_name()
	cmd = cmd and basename(cmd) or ""

	-- Time
	local time = wezterm.strftime("%H:%M")

	-- Right status
	window:set_right_status(wezterm.format({
		{ Text = wezterm.nerdfonts.md_folder .. "  " .. cwd },
		{ Text = " | " },
		{ Foreground = { Color = "#e0af68" } },
		{ Text = wezterm.nerdfonts.fa_code .. "  " .. cmd },
		"ResetAttributes",
		{ Text = " | " },
		{ Text = wezterm.nerdfonts.md_clock .. "  " .. time },
		{ Text = "  " },
	}))
end)



-- terminal functionality
config.enable_scroll_bar = true
config.scrollback_lines = 5000

-- Workspace
config.default_workspace = "main"



-- key bindings
config.keys = {
  -- Ctrl+Shift+C to copy selection to system clipboard via wl-copy
  {
	key = "C",
	mods = "CTRL|SHIFT",
	action = wezterm.action.Multiple({
	  wezterm.action.CopyTo("ClipboardAndPrimarySelection"),
	  wezterm.action.EmitEvent("trigger-copy-to-clipboard"),
	}),
  },
  -- Ctrl+Shift+V to paste from clipboard
  {
	key = "V",
	mods = "CTRL|SHIFT",
	action = wezterm.action.PasteFrom("Clipboard"),
  },
  -- Ctrl+Shift+K to close current pane
  {
  key = "K",
  mods = "CTRL|SHIFT",
  action = wezterm.action.CloseCurrentPane { confirm = true },
  }
}

-- Auto-copy any selection
-- config.copy_on_select = true

-- Copy selection to Wayland system clipboard via wl-copy
wezterm.on("trigger-copy-to-clipboard", function(window, pane)
  local sel = window:get_selection_text_for_pane(pane)
  if sel and sel ~= "" then
    local handle = io.popen("wl-copy", "w")
    handle:write(sel)
    handle:close()
  end
end)

return config
