use std::borrow::Cow::Borrowed;
use std::collections::HashMap;
use pyo3::prelude::*;
use crate::info::VERSION;

use crate::prelude::*;
use crate::render::html::HtmlRender;
use crate::render::text::TextRender;


fn render<R: Render>(
    text: &mut String,
    renderer: &R) -> R::Output
{
    // TODO includer
    let page_info = page_info_dummy();
    let settings = WikitextSettings::from_mode(WikitextMode::Page);

    crate::preprocess(text);
    let tokens = crate::tokenize(&text);
    let (tree, _warnings) = crate::parse(&tokens, &page_info, &settings).into();
    let output = renderer.render(&tree, &page_info, &settings);
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


#[pyfunction]
fn render_html(
    source: &str) -> PyResult<HashMap<String, String>>
{
    let html_output = render(&mut source.to_string(), &HtmlRender);

    let mut output = HashMap::new();
    output.insert(String::from("body"), html_output.body);
    output.insert(String::from("style"), html_output.styles.join("\n"));

    Ok(output)
}


#[pyfunction]
fn render_text(
    source: &str) -> PyResult<String>
{
    Ok(render(&mut source.to_string(), &TextRender))
}


#[pymodule]
fn ftml(
    _py: Python,
    m: &PyModule) -> PyResult<()> {

    m.add("ftml_version", VERSION.to_string())?;
    m.add_function(wrap_pyfunction!(render_html, m)?)?;
    m.add_function(wrap_pyfunction!(render_text, m)?)?;

    Ok(())
}
