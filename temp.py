import argparse
import sys
import imgui
import glfw
import imgui
from imgui.integrations.glfw import GlfwRenderer
import OpenGL.GL as gl


def impl_glfw_init():
    width, height = 1600, 900
    window_name = "minimal ImGui/GLFW3 example"

    if not glfw.init():
        print("Could not initialize OpenGL context")
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

    window = glfw.create_window(int(width), int(height), window_name, None, None)
    glfw.make_context_current(window)

    if not window:
        glfw.terminate()
        print("Could not initialize Window")
        sys.exit(1)

    return window


def render_frame(impl, window, value_old):
    glfw.poll_events()
    impl.process_inputs()
    imgui.new_frame()

    gl.glClearColor(0.1, 0.1, 0.1, 1)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    value_old = frame_commands(value_old)

    imgui.render()
    impl.render(imgui.get_draw_data())
    glfw.swap_buffers(window)

    return value_old


def frame_commands(value_old=""):
    gl.glClearColor(0.1, 0.1, 0.1, 1)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    io = imgui.get_io()

    # shortcuts
    if io.key_ctrl and io.keys_down[glfw.KEY_Q]:
        sys.exit(0)

    # menu bar
    if imgui.begin_main_menu_bar():
        if imgui.begin_menu("Menu", True):
            clicked_quit, selected_quit = imgui.menu_item("Quit", "Ctrl+Q", False, True)

            if clicked_quit:
                sys.exit(0)

            imgui.end_menu()
        imgui.end_main_menu_bar()

    # main window
    imgui.begin("Crop file(s)")

    if imgui.text("Files to be cropped"):
        pass

    # input files
    changed, value = imgui.input_text_multiline("", "Files to be cropped", 99999999)

    # Crop button
    # if imgui.button("Crop file(s)"):
    if value != value_old:
        value_old = value_old
        print("Cropping...")
        print(value)

    # end main window
    imgui.end()

    return value_old


def main():

    # initialise
    imgui.create_context()

    # ask os for window
    window = impl_glfw_init()
    impl = GlfwRenderer(window)

    value_old = ""
    while not glfw.window_should_close(window):
        value_old = render_frame(impl, window, value_old)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()

