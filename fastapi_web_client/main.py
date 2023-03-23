from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from schemas import APIUserInput
import crud
import context_processors as cp

app = FastAPI()


templates = Jinja2Templates(directory="templates",
                            context_processors=[cp.placeholder_processor,
                                                cp.invalid_massage_processor,
                                                cp.default_values_processor,
                                                cp.default_units_processor,
                                                cp.allowed_range_processor,
                                                ])

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def sensitivity_calculator(request: Request):

    return templates.TemplateResponse("sensitivity_calculator.html",
                                      {"request": request, "params_vals_units": crud.get_param_values_units()})


@app.post("/v1/sensitivity")
async def sensitivity(api_user_input: APIUserInput):

    user_input = _unpack_api_user_input(api_user_input)

    try:
        return crud.do_calculation(user_input, "sensitivity")
    except crud.UserInputError as e:
        raise HTTPException(status_code=400, detail=e.message)


@app.post("/v1/integration-time")
async def t_int(api_user_input: APIUserInput):

    user_input = _unpack_api_user_input(api_user_input)

    try:
        return crud.do_calculation(user_input, "integration_time")
    except crud.UserInputError as e:
        raise HTTPException(status_code=400, detail=e.message)


@app.get("/v1/param-values-units")
async def param_values_units():
    return crud.get_param_values_units()


def _unpack_api_user_input(api_user_input):
    return {
        "t_int": api_user_input.t_int,
        "sensitivity": api_user_input.sensitivity,
        "bandwidth": api_user_input.bandwidth,
        "obs_freq": api_user_input.obs_freq,
        "n_pol": api_user_input.n_pol,
        "weather": api_user_input.weather,
        "elevation": api_user_input.elevation,
    }
