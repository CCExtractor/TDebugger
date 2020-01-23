import importlib.util
import sys
import copy
import time
import os
from datetime import datetime
import argparse
import json
import pickle
import inspect
from PIL import Image, ImageDraw, ImageFont
import cv2 as cv2
import numpy
import yaml
import textwrap


class TD:
    def __init__(self, name, line, step, value):
        self.name = name
        self.line_value = []
        self.incrementor(line, step, value)

    def incrementor(self, line, step, value):
        self.line_value.append({"line": line, "step": step, "value": value})

    def getvariabletype(self):
        value = self.line_value[0]["value"]
        t = type(value)
        for lv in self.line_value:
            if type(lv["value"]) != t:
                return "undefined"
        return t

    def range(self):
        if self.getvariabletype() in [int, float]:
            values = [lv["value"] for lv in self.line_value]
            return [min(values), max(values)]

    def dictionary(self):
        return {"var": self.name, "type": str(self.getvariabletype()), "range": self.range(), "vallogs": self.line_value}


class Line:
    def __init__(self, line_num):
        self.line_num = line_num
        self.times_executed = 0
        self.total_time = 0

    def run_line(self, time):
        self.times_executed += 1
        self.total_time += time

    def dictionary(self):
        return {"line_num": self.line_num, "times_executed": self.times_executed, "total_time": self.total_time}


class TDebugger:
    def __init__(self, file_path, function_name, function_args):
        self.file_path = file_path
        self.function_name = function_name
        self.function_args = function_args

        self.curr_line = None
        self.prev_variables = {}
        self.variablelogs = {}
        self.linelogs = {}
        self.prev_time = time.time()
        self.step = 0

        self.results = {"code_info": {"filename": os.path.split(self.file_path)[1], "function_name": self.function_name, "function_args": self.function_args}, "logs": [],
                        "variablelogs": [], "linelogs": []}

    def __trace_calls(self, frame, event, arg):
        self.curr_line = frame.f_lineno
        if frame.f_code.co_name == self.function_name:
            return self.__trace_lines

    def __trace_lines(self, frame, event, arg):
        curr_logs = {"step": self.step, "timestamp": time.time(
        ), "line_num": self.curr_line, "actions": []}
        self.results["logs"].append(curr_logs)

        if self.curr_line not in self.linelogs:
            self.linelogs[self.curr_line] = Line(self.curr_line)
        self.linelogs[self.curr_line].run_line(
            time.time() - self.prev_time)
        curr_logs["line_runtime"] = self.linelogs[self.curr_line].dictionary(
        )

        self.first_print_for_this_line = True
        current_variables = frame.f_locals
        for var, val in current_variables.items():
            if var not in self.prev_variables:
                curr_logs["actions"].append(
                    {"action": "init_var", "var": var, "val": val})
                self.variablelogs[var] = TD(
                    var, self.curr_line, self.step, copy.deepcopy(val))
            elif self.prev_variables[var] != val:
                prev_val = self.prev_variables[var]
                if isinstance(prev_val, list) and isinstance(val, list):
                    self.debuglist(var, prev_val, val)
                elif isinstance(prev_val, dict) and isinstance(val, dict):
                    self.debugdict(var, prev_val, val)
                else:
                    curr_logs["actions"].append(
                        {"action": "change_var", "var": var, "prev_val": prev_val, "new_val": val})
                self.variablelogs[var].incrementor(
                    self.curr_line, self.step, copy.deepcopy(val))

        self.prev_variables = copy.deepcopy(current_variables)
        self.prev_time = time.time()
        self.curr_line = frame.f_lineno
        self.step += 1

    def debuglist(self, var, prev_val, val):
        curr_logs = self.results["logs"][-1]

        for i in range(min(len(val), len(prev_val))):
            if val[i] != prev_val[i]:
                curr_logs["actions"].append(
                    {"action": "list_change", "var": var, "index": i, "prev_val": prev_val[i], "new_val": val[i]})
        if len(val) > len(prev_val):
            for i in range(len(prev_val), len(val)):
                curr_logs["actions"].append(
                    {"action": "list_add", "var": var, "index": i, "val": val[i]})
        if len(val) < len(prev_val):
            for i in range(len(val), len(prev_val)):
                curr_logs["actions"].append(
                    {"action": "list_remove", "var": var, "index": i})

    def debugdict(self, var, prev_val, val):
        curr_logs = self.results["logs"][-1]

        for elem in val:
            if elem not in prev_val:
                curr_logs["actions"].append(
                    {"action": "dict_add", "var": var, "key": elem, "val": val[elem]})
            elif prev_val[elem] != val[elem]:
                curr_logs["actions"].append(
                    {"action": "dict_change", "var": var, "key": elem, "prev_val": prev_val[elem], "new_val": val[elem]})
        for elem in prev_val:
            if elem not in val:
                curr_logs["actions"].append(
                    {"action": "dict_remove", "var": var, "key": elem})

    def run(self):
        module_spec = importlib.util.spec_from_file_location(
            "debugger", self.file_path)
        module = importlib.util.module_from_spec(module_spec)
        # print(module),
        module_spec.loader.exec_module(module)
        function = getattr(module, self.function_name)

        sys.settrace(self.__trace_calls)
        self.prev_time = time.time()
        function(*self.function_args)
        sys.settrace(None)

        self.results["variablelogs"] = [var_obj.dictionary()
                                        for var_obj in self.variablelogs.values()]
        self.results["linelogs"] = [line_obj.dictionary()
                                    for line_obj in self.linelogs.values()]

        return self.results


class VideoOutput:
    def __init__(self, file_path, func_name, results, config):
        module_spec = importlib.util.spec_from_file_location(
            "sourcemodule", file_path)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        func = getattr(module, func_name)

        self.source_lines, self.start_line = inspect.getsourcelines(func)
        self.results = results
        with open(config) as configuration:
            self.config = yaml.safe_load(configuration)
            with open(os.path.dirname(__file__) + "/themes/" + self.config["theme"] + ".yaml") as theme_file:
                self.color_theme = yaml.safe_load(theme_file)

    def themer(self, font, text, max_width):
        num_chars = len(text)
        while font.getsize_multiline(textwrap.fill(text, num_chars))[0] >= max_width:
            num_chars -= 1

        return textwrap.fill(text, num_chars)

    def introthemer(self):
        intro = self.config["intro-text"]["text"]
        aspect_ratio = (self.config["size"]["width"],
                        self.config["size"]["height"])
        img = Image.new("RGB", aspect_ratio,
                        color=self.color_theme["background-color"])

        font = ImageFont.truetype(os.path.dirname(__file__) + "./fonts/{}.ttf".format(self.config["fonts"]["intro-text"]["font-family"]),
                                  self.config["fonts"]["intro-text"]["font-size"])
        draw = ImageDraw.Draw(img)
        intro = self.themer(font, intro, aspect_ratio[0] * 0.8)
        introsize = font.getsize_multiline(intro)
        text_start_x, text_start_y = (
            aspect_ratio[0] - introsize[0]) / 2, (aspect_ratio[1] - introsize[1]) / 2

        draw.text((text_start_x, text_start_y), intro,
                  font=font, fill=self.color_theme["normaltext"])

        return img

    def framer(self, current_step, variablelogs):
        font_size = self.config["fonts"]["default"]["font-size"]
        aspect_ratio = (self.config["size"]["width"],
                        self.config["size"]["height"])

        img = Image.new("RGB", aspect_ratio,
                        color=self.color_theme["background-color"])

        font = ImageFont.truetype(os.path.dirname(__file__) + "./fonts/{}.ttf".format(
            self.config["fonts"]["default"]["font-family"]), self.config["fonts"]["default"]["font-size"])
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, (current_step['line_num'] - self.start_line) * font_size, aspect_ratio[0] * 0.4, (current_step['line_num'] - self.start_line + 1) * font_size),
                       fill=self.color_theme["current-line-color"])
        for line_offset, line in enumerate(self.source_lines):
            draw.text((0, line_offset * font_size),
                      self.source_lines[line_offset], fill=self.color_theme["normaltext"])

        draw.text((0, aspect_ratio[1] * 0.8), "Step: {}, line: {}".format(
            current_step['step'], current_step['line_num']), fill=self.color_theme["normaltext"])
        draw.text((0, aspect_ratio[1] * 0.8 + font_size),
                  "Times executed: {}, time spent: {}s".format(
                      current_step['line_runtime']['times_executed'], "{0:.7f}".format(current_step['line_runtime']['total_time'])),
                  fill=self.color_theme["normaltext"])

        current_text_y = 0
        variable_changes = {}
        for action in current_step["actions"]:
            action_desc = "Illegal action"
            if action["action"] == "init_var":
                action_desc = "created"
            elif action["action"] == "change_var":
                action_desc = "previous value {}".format(action["prev_val"])
            elif action["action"] == "list_add":
                action_desc = "{}[{}] appended with value {}".format(
                    action["var"], action["index"], action["val"])
            elif action["action"] == "list_change":
                action_desc = "{}[{}] changed from {} to {}".format(
                    action["var"], action["index"], action["prev_val"], action["new_val"])
            elif action["action"] == "list_remove":
                action_desc = "{}[{}] removed".format(
                    action["var"], action["index"])
            elif action["action"] == "dict_add":
                action_desc = "key {} added with value {}".format(
                    action["key"], action["val"])
            elif action["action"] == "dict_change":
                action_desc = "value of key {} changed from {} to {}".format(
                    action["key"], action["prev_val"], action["new_val"])
            elif action["action"] == "dict_remove":
                action_desc = "key {} removed".format(action["key"])

            if action["var"] not in variable_changes:
                variable_changes[action["var"]] = []
            variable_changes[action["var"]].append(action_desc)

        for variable in variablelogs:
            curr_value = None
            for val in variable['vallogs']:
                if val['step'] > current_step['step']:
                    break
                curr_value = val["value"]

            if variable['var'] in variable_changes:
                message = "Variable {}, value {}, ".format(
                    variable['var'], curr_value) + ", ".join(variable_changes[variable['var']]) + "."
                draw.text((aspect_ratio[0] * 0.4 + 5, current_text_y),
                          message, fill=self.color_theme["updatingtext"])
            elif curr_value is not None:
                draw.text((aspect_ratio[0] * 0.4 + 5, current_text_y), "Variable {}, value {}.".format(
                    variable['var'], curr_value), fill=self.color_theme["normaltext"])
            current_text_y += font_size
        separating_line_color = self.color_theme["separating-line-color"]
        draw.line((aspect_ratio[0] * 0.4, 0, aspect_ratio[0] *
                   0.4, aspect_ratio[1]), fill=separating_line_color, width=2)
        draw.line((0, aspect_ratio[1] * 0.8, aspect_ratio[0] * 0.4,
                   aspect_ratio[1] * 0.8), fill=separating_line_color, width=2)
       # print(self.config["watermark"])
        if self.config["watermark"]:

            text_width, text_height = 500, 10
            draw.text((aspect_ratio[0] - text_width, aspect_ratio[1] - text_height),
                      "Created using TDebugger", fill=self.color_theme["normaltext"])

        return img

    def generate_video(self, output_path):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        aspect_ratio = (self.config["size"]["width"],
                        self.config["size"]["height"])
        fps = self.config["fps"]
        video = cv2.VideoWriter(output_path, fourcc, fps, aspect_ratio)
        if self.config["intro-text"]["text"]:
            intro_img = self.introthemer()
            num_intro_frames = fps * self.config["intro-text"]["time"]
            for _ in range(num_intro_frames):
                video.write(cv2.cvtColor(
                    numpy.array(intro_img), cv2.COLOR_RGB2BGR))

        for step in self.results["logs"]:
            img = self.framer(
                step, self.results["variablelogs"])
            video.write(cv2.cvtColor(numpy.array(img), cv2.COLOR_RGB2BGR))

        video.release()


class Terminal:
    def __init__(self, results):
        self.results = results

    def terminal(self):

        logs = self.results["logs"]
        for step in logs:
            print("{} - Step {}, line {} - executed {} times so far, total time so far {}s, average time so far {}s".format(
                datetime.utcfromtimestamp(step["timestamp"]).strftime(
                    '%Y-%m-%d %H:%M:%S'), step["step"], step["line_num"], step["line_runtime"]["times_executed"],
                "{0:0.07f}".format(step["line_runtime"]["total_time"]), "{0:0.07f}".format(step["line_runtime"]["total_time"] / step["line_runtime"]["times_executed"],),),)

            print("", end="")
            if step["actions"]:
                first = True
                for action in step["actions"]:
                    if first:
                        first = False
                    else:
                        print(", ", end="")

                    if action["action"] == "init_var":
                        action_desc = "variable '{}' created and initiated with {}".format(
                            action["var"], action["val"])
                    elif action["action"] == "change_var":
                        action_desc = "variable '{}' changed from {} to {}".format(
                            action["var"], action["prev_val"], action["new_val"])
                    elif action["action"] == "rm_var":
                        action_desc = "variable '{}' is deleted from memory {} to {}".format(
                            action["var"], action["prev_val"], action["None"])
                    elif action["action"] == "list_add":
                        action_desc = "{}[{}] appended with value {}".format(
                            action["var"], action["index"], action["val"])
                    elif action["action"] == "list_change":
                        action_desc = "{}[{}] changed from {} to {}".format(
                            action["var"], action["index"], action["prev_val"], action["new_val"])
                    elif action["action"] == "list_remove":
                        action_desc = "{}[{}] removed".format(
                            action["var"], action["index"])
                    elif action["action"] == "dict_add":
                        action_desc = "key {} added to {} with value {}".format(
                            action["key"], action["var"], action["val"])
                    elif action["action"] == "dict_change":
                        action_desc = "value of key {} in {} changed from {} to {}".format(
                            action["key"], action["var"], action["prev_val"], action["new_val"])
                    elif action["action"] == "dict_remove":
                        action_desc = "key {} removed from {}".format(
                            action["key"], action["var"])
                    print(action_desc, end="")
                print("")
        print()

        linelogs = self.results["linelogs"]
        print("", end="")
        for line in linelogs:
            print("Line {}: executed {} times, total runtime {}s, average time so far {}s".format(line["line_num"], line["times_executed"],
                                                                                                  "{0:0.07f}".format(
                line["total_time"]),
                "{0:0.07f}".format(step["line_runtime"]["total_time"] / step["line_runtime"]["times_executed"],),),)
        print("", end="")


def funcarg(argument):
    try:
        return int(argument)
    except ValueError:
        try:

            return float(argument)
        except ValueError:
            return argument


def main():

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)

    debugGroup = parser.add_argument_group(
        title="Analysis")
    debugGroup.add_argument("--debug", "-d",  help=".\n".join(
        ["Path of a *.py file to debug", "Example: '--debug/-d main.py' will run the file main.py."]), metavar="FILE")
    debugGroup.add_argument("--function", "-f", help=".\n".join(
        ["If --debug FILE is present, optionally provide the name of a function to debug and function arguments", "(defaults to main with no arguments)",
         "Example: '--func/-f foo 10' will run foo(10)."]), nargs='+', default=["main"], metavar=("FUNC", "PARAMETER"))

    debugGroup.add_argument("--output", "-o", help="./n".join(
        ["will output the logs in result.json file \nIMPORTANT name output file 'result.json' if you want to create a video later, \nExample: ' TDebugger -d foo.py -f test2 10 -o result.json'"]), metavar="FILE")

    printGroup = parser.add_argument_group(
        title="Reporting")
    printGroup.add_argument("--parse", "-p", help="./n".join(
        ["parses a .json file(eg. the result.json file created with --output/-o argument) file in readable format."]), metavar="FILE")
    videoGroup = parser.add_argument_group(
        title="Video Reporting", description="Generating a video displaying the program's flow and execution.")
    videoGroup.add_argument("--video", "-v",
                            metavar=("PYTHON_FILE", "FUNCTION", "ANALYSIS_FILE", "VIDEO_OUTPUT"), nargs=4)
    videoGroup.add_argument("--config", "-c", help="Path of video config file, in .yaml format. \nExample: '--config/-c ./config.yaml'",
                            default=os.path.dirname(__file__) + "/config.yaml")
    args = parser.parse_args()

    if args.debug:
        debugpwd = args.debug
        function_name = args.function[0]
        function_args = list([funcarg(arg) for arg in args.function[1:]])

        tdebugger = TDebugger(debugpwd, function_name,
                              function_args)
        results = tdebugger.run()

        outputpwd = args.output
        if outputpwd:
            with open(outputpwd, "w") as f:
                json.dump(results, f)
        else:
            terminal = Terminal(results)
            terminal.terminal()
        with open(
                "./result.json", "wb") as f:
            pickle.dump(results, f)

    elif args.parse:
        parse_file_path = args.parse
        with open(parse_file_path) as f:
            data = json.load(f)
        terminal = Terminal(data)
    elif args.video:
        with open(args.video[2], "rb") as f:
            parsed_data = pickle.load(f)
        reporter = VideoOutput(
            args.video[0], args.video[1], parsed_data, args.config)
        reporter.generate_video(args.video[3])
    else:
        print("Run <<\"TDebugger --help\">>")
