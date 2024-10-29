use super::prelude::*;

use crate::data::ExpressionResult;

use std::borrow::Cow;

pub const BLOCK_SCOPE: BlockRule = BlockRule {
    name: "block-scpoe",
    accepts_names: &["scope"],
    accepts_star: false,
    accepts_score: false,
    accepts_newlines: true,
    accepts_partial: AcceptsPartial::None,
    parse_fn: parse_scope,
};

pub const BLOCK_DECLARE: BlockRule = BlockRule {
    name: "block-declare",
    accepts_names: &["declare"],
    accepts_star: true,
    accepts_score: true,
    accepts_newlines: false,
    accepts_partial: AcceptsPartial::None,
    parse_fn: parse_var,
};

pub const BLOCK_SET: BlockRule = BlockRule {
    name: "block-set",
    accepts_names: &["set"],
    accepts_star: true,
    accepts_score: true,
    accepts_newlines: false,
    accepts_partial: AcceptsPartial::None,
    parse_fn: parse_var,
};

fn parse_scope<'r, 't>(
    parser: &mut Parser<'r, 't>,
    name: &'t str,
    flag_star: bool,
    flag_score: bool,
    in_head: bool,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Parsing scope block (name {name}, in-head {in_head})");
    assert!(!flag_star, "WikiScript scopes doesn't allow star flag");
    assert!(!flag_score, "WikiScript scopes doesn't allow score flag");

    // syntax:
    // [[scope]]
    // ... var context ...
    // [[/scope]]

    assert_block_name(&BLOCK_SCOPE, name);
    
    parser.push_scope();

    let arguments = parser.get_head_map(&BLOCK_SCOPE, in_head)?;

    let (elements, exceptions, _) = parser
        .get_body_elements(&BLOCK_SCOPE, name, false)?
        .into();

    let element = Element::Container(Container::new(
        ContainerType::WSScope,
        elements,
        arguments.to_attribute_map(parser.settings()),
    ));

    parser.pop_scope();

    ok!(element, exceptions)

}

fn parse_var<'r, 't>(
    parser: &mut Parser<'r, 't>,
    name: &'t str,
    flag_star: bool,
    flag_score: bool,
    in_head: bool,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Parsing WikiScript variable block (name {name}, in-head {in_head})");
    assert!(!flag_score, "WikiScript variables doesn't allow score flag");

    // syntax: [[declare name value]]
    //         [[set name value]]

    let condition = collect_text(
        parser,
        parser.rule(),
        &[],
        &[ParseCondition::current(Token::RightBlock)],
        &[],
        None,
    )?;

    let mut params = condition.splitn(2," ");

    let var_name = match params.next() {
        Some(param) => param,
        None => ""
    };

    let mut expr = match params.next() {
        Some(param) => Cow::Borrowed(param),
        None => Cow::Borrowed("")
    };

    if var_name == "" || expr == "" {
        return Err(parser.make_warn(ParseWarningKind::NoSuchVariable));
    }

    parser.replace_variables(expr.to_mut());


    let value = if flag_star {
        Cow::from(evaluate_expr(parser, &expr).to_string())
    } else {
        Cow::from(expr)
    };

    parser.push_variable(Cow::Borrowed(var_name), value.clone(), name == "declare");

    let transaction = &mut parser.transaction(ParserTransactionFlags::Scopes);

    transaction.commit();

    ok!(Element::Void)
}

fn evaluate_expr<'r, 't>(parser: &mut Parser<'r, 't>, expr: &str) -> ExpressionResult<'static> {
    parser.page_callbacks().evaluate_expression(Cow::Borrowed(expr))
}
