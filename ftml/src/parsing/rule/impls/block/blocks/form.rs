use std::borrow::Cow;

use crate::tree::FormInput;

use super::prelude::*;

pub const BLOCK_FORM: BlockRule = BlockRule {
    name: "block-form",
    accepts_names: &["form"],
    accepts_star: false,
    accepts_score: true,
    accepts_newlines: false,
    accepts_partial: AcceptsPartial::None,
    parse_fn: parse_form,
};

fn parse_form<'r, 't>(
    parser: &mut Parser<'r, 't>,
    name: &'t str,
    flag_star: bool,
    flag_score: bool,
    in_head: bool,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Parsing form block (name '{name}', in-head {in_head})");
    assert!(!flag_star, "Form doesn't allow star flag");
    assert_block_name(&BLOCK_FORM, name);

    let mut arguments = parser.get_head_map(&BLOCK_FORM, in_head)?;

    // Get body content, without paragraphs
    let (elements, exceptions, paragraph_safe) = parser
        .get_body_elements(&BLOCK_FORM, name, !flag_score)?
        .into();

    let class = arguments.get("class").unwrap_or(Cow::from(""));
    let target = match arguments.get("target") {
        Some(target) => {
            if target == "." {
                parser.page_info().full_name()
            } else {
                target
            }
        },
        None => parser.page_info().full_name(),
    };

    let mut attributes = arguments.to_attribute_map(parser.settings());
    attributes.insert("data-target-page", target.to_owned());
    attributes.insert("class", Cow::Owned(format!("w-ref-form {class}")));

    let element = Element::Container(Container::new(
        ContainerType::Form,
        elements,
        attributes,
    ));

    ok!(paragraph_safe; element, exceptions)
}

pub const BLOCK_FORM_INPUT: BlockRule = BlockRule {
    name: "block-form-input",
    accepts_names: &["input"],
    accepts_star: false,
    accepts_score: false,
    accepts_newlines: false,
    accepts_partial: AcceptsPartial::None,
    parse_fn: parse_form_input,
};

fn parse_form_input<'r, 't>(
    parser: &mut Parser<'r, 't>,
    name: &'t str,
    flag_star: bool,
    flag_score: bool,
    in_head: bool,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Parsing form input block (name '{name}', in-head {in_head})");
    assert!(!flag_star, "Form input doesn't allow star flag");
    assert!(!flag_score, "Form input doesn't allow score flag");
    assert_block_name(&BLOCK_FORM_INPUT, name);

    let arguments = parser.get_head_map(&BLOCK_FORM, in_head)?;

    let element = Element::FormInput(FormInput{ attributes: arguments.to_attribute_map(parser.settings()) });

    ok!(true; element, vec![])
}