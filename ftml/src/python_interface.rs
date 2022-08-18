use std::borrow::Cow;
use std::borrow::Cow::Borrowed;
use std::collections::HashMap;
use std::fmt::{Debug, Formatter};
use std::rc::Rc;

use pyo3::prelude::*;

use crate::info::VERSION;
use crate::prelude::*;
use crate::render::html::HtmlRender;
use crate::render::text::TextRender;

fn render<R: Render>(text: &mut String, renderer: &R, page_info: PageInfo, callbacks: Py<PyAny>) -> R::Output
{
    // TODO includer
    let settings = WikitextSettings::from_mode(WikitextMode::Page);

    let page_callbacks = Rc::new(PythonCallbacks{ callbacks: Box::new(callbacks) }).clone();

    preprocess(text);
    let tokens = tokenize(text);
    let (tree, _warnings) = parse(&tokens, &page_info, page_callbacks.clone(), &settings).into();
    let output = renderer.render(&tree, &page_info, page_callbacks.clone(), &settings);
    output
}


fn page_info_dummy() -> PageInfo<'static>
{
    PageInfo {
        page: Borrowed("some-page"),
        category: None,
        site: Borrowed("sandbox"),
        title: Borrowed("title"),
        alt_title: None,
        rating: 0.0,
        tags: vec![],
        language: Borrowed("default")
    }
}

struct PythonCallbacks {
    callbacks: Box<Py<PyAny>>,
}

impl Debug for PythonCallbacks {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        write!(f, "<PythonCallbacks>")
    }
}

impl PageCallbacks for PythonCallbacks {
    fn module_has_body(&self, module_name: Cow<str>) -> bool {
        let result = Python::with_gil(|py| {
            return self.callbacks.getattr(py, "module_has_body")?.call(py, (module_name,), None)?.extract(py);
        });
        match result {
            Ok(result) => result,
            Err(_) => false
        }
    }

    fn render_module(&self, module_name: Cow<str>, params: HashMap<Cow<str>, Cow<str>>, body: Cow<str>) -> Cow<'static, str> {
        let py_params: HashMap<String, String> = params.keys().fold(HashMap::new(), |mut acc, k| {
            acc.insert(k.to_string(), params.get(k).unwrap().to_string());
            acc
        });
        let result: PyResult<String> = Python::with_gil(|py| {
            return self.callbacks.getattr(py, "render_module")?.call(py, (module_name, py_params, body), None)?.extract(py);
        });
        match result {
            Ok(result) => Cow::from(result.as_str().to_owned()),
            Err(_) => Cow::from("")
        }
    }
}


#[pyclass(subclass)]
struct Callbacks {}

#[pymethods]
impl Callbacks {
    #[new]
    fn new() -> Self {
        Callbacks{}
    }

    pub fn module_has_body(&self, _module_name: String) -> PyResult<bool> {
        return Ok(false)
    }

    pub fn render_module(&self, _module_name: String, _params: HashMap<String, String>, _body: String) -> PyResult<String> {
        return Ok("".to_string())
    }
}

#[pyfunction(kwargs="**")]
fn render_html(source: String, callbacks: Py<PyAny>) -> PyResult<HashMap<String, String>>
{
    let html_output = render(&mut source.to_string(), &HtmlRender, page_info_dummy(), callbacks);

    let mut output = HashMap::new();
    output.insert(String::from("body"), html_output.body);
    output.insert(String::from("style"), html_output.styles.join("\n"));

    Ok(output)
}


#[pyfunction(kwargs="**")]
fn render_text(source: String, callbacks: Py<PyAny>) -> PyResult<String>
{
    Ok(render(&mut source.to_string(), &TextRender, page_info_dummy(), callbacks))
}


#[pymodule]
fn ftml(_py: Python, m: &PyModule) -> PyResult<()> {

    m.add("ftml_version", VERSION.to_string())?;
    m.add_function(wrap_pyfunction!(render_html, m)?)?;
    m.add_function(wrap_pyfunction!(render_text, m)?)?;
    m.add_class::<Callbacks>()?;

    Ok(())
}
