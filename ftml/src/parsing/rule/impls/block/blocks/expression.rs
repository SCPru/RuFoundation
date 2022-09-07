/*
 * parsing/rule/impls/block/blocks/image.rs
 *
 * ftml - Library to parse Wikidot text
 * Copyright (C) 2019-2022 Wikijump Team
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

use std::borrow::Cow;

use crate::{data::ExpressionResult, tree::PartialElement};

use super::prelude::*;

pub const BLOCK_IF: BlockRule = BlockRule {
    name: "block-if",
    accepts_names: &["#if", "#ifexpr"],
    accepts_star: false,
    accepts_score: false,
    accepts_newlines: false,
    accepts_partial: AcceptsPartial::None,
    parse_fn,
};

pub const BLOCK_IF_WITH_BODY: BlockRule = BlockRule {
    name: "block-if-body",
    accepts_names: &["if"],
    accepts_star: false,
    accepts_score: false,
    accepts_newlines: false,
    accepts_partial: AcceptsPartial::Else,
    parse_fn: parse_if_with_body,
};

pub const BLOCK_IFEXPR_WITH_BODY: BlockRule = BlockRule {
    name: "block-ifexpr-body",
    accepts_names: &["ifexpr"],
    accepts_star: false,
    accepts_score: false,
    accepts_newlines: false,
    accepts_partial: AcceptsPartial::Else,
    parse_fn: parse_ifexpr_with_body,
};

pub const BLOCK_IF_ELSE: BlockRule = BlockRule {
    name: "block-if-else",
    accepts_names: &["else"],
    accepts_star: false,
    accepts_score: false,
    accepts_newlines: false,
    accepts_partial: AcceptsPartial::None,
    parse_fn: parse_if_else,
};

pub const BLOCK_EXPR: BlockRule = BlockRule {
    name: "block-expr",
    accepts_names: &["#expr"],
    accepts_star: false,
    accepts_score: false,
    accepts_newlines: false,
    accepts_partial: AcceptsPartial::None,
    parse_fn: parse_expr,
};

fn parse_fn<'r, 't>(
    parser: &mut Parser<'r, 't>,
    name: &'t str,
    flag_star: bool,
    flag_score: bool,
    in_head: bool,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Parsing expression block (name {name}, in-head {in_head})");
    assert!(!flag_star, "Expression doesn't allow star flag");
    assert!(!flag_score, "Expression doesn't allow score flag");

    // syntax: [[#if|#ifexpr condition | truthy nodes | falsey nodes]]

    let condition = collect_text(
        parser,
        parser.rule(),
        &[],
        &[ParseCondition::current(Token::Pipe)],
        &[],
        None,
    )?;

    let truthy_raw = collect_consume_keep(
        parser,
        parser.rule(),
        &[],
        &[ParseCondition::current(Token::RightBlock), ParseCondition::current(Token::Pipe)],
        &[],
        None
    )?;

    let truthy = ParseSuccess::new(truthy_raw.item.0, truthy_raw.exceptions, truthy_raw.paragraph_safe);

    let falsey = match truthy_raw.item.1.token {
        Token::Pipe => collect_consume(
            parser,
            parser.rule(),
            &[],
            &[ParseCondition::current(Token::RightBlock)],
            &[],
            None
        )?,
        Token::RightBlock => ParseSuccess::new(vec![], vec![], true),
        _ => return Err(parser.make_warn(ParseWarningKind::RuleFailed))
    };

    // evaluate right away; 
    match name {
        "#if" => {
            if evaluate_if(parser, condition) {
                ok!(truthy.paragraph_safe; truthy.item, truthy.exceptions)
            } else {
                ok!(truthy.paragraph_safe; falsey.item, truthy.exceptions)
            }
        }
        "#ifexpr" => {
            if evaluate_ifexpr(parser, condition) {
                ok!(truthy.paragraph_safe; truthy.item, truthy.exceptions)
            } else {
                ok!(truthy.paragraph_safe; falsey.item, truthy.exceptions)
            }
        }
        _ => unreachable!()
    }
}

fn parse_if_with_body<'r, 't>(
    parser: &mut Parser<'r, 't>,
    name: &'t str,
    flag_star: bool,
    flag_score: bool,
    in_head: bool,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Parsing expression block (name {name}, in-head {in_head}; with body)");
    assert!(!flag_star, "Expression doesn't allow star flag");
    assert!(!flag_score, "Expression doesn't allow score flag");

    parse_with_body(parser, name, &BLOCK_IF_WITH_BODY)
}

fn parse_ifexpr_with_body<'r, 't>(
    parser: &mut Parser<'r, 't>,
    name: &'t str,
    flag_star: bool,
    flag_score: bool,
    in_head: bool,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Parsing expression block (name {name}, in-head {in_head}; with body)");
    assert!(!flag_star, "Expression doesn't allow star flag");
    assert!(!flag_score, "Expression doesn't allow score flag");

    parse_with_body(parser, name, &BLOCK_IFEXPR_WITH_BODY)
}

fn parse_if_else<'r, 't>(
    _parser: &mut Parser<'r, 't>,
    name: &'t str,
    flag_star: bool,
    flag_score: bool,
    in_head: bool,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Parsing else block (name {name}, in-head {in_head})");
    assert!(!flag_star, "Else doesn't allow star flag");
    assert!(!flag_score, "Else doesn't allow score flag");
    assert_block_name(&BLOCK_IF_ELSE, name);

    ok!(true; Element::Partial(PartialElement::Else), vec![])
}

fn parse_with_body<'r, 't>(parser: &mut Parser<'r, 't>, name: &'t str, rule: &BlockRule) -> ParseResult<'r, 't, Elements<'t>> {
    // syntax: [[if|ifexpr condition]]truthy nodes[[else]]falsey nodes[[/if|ifexpr]]

    let condition = collect_text(
        parser,
        parser.rule(),
        &[],
        &[ParseCondition::current(Token::RightBlock)],
        &[],
        None,
    )?;

    // Get body content, never with paragraphs
    let (elements, _, _) =
        parser.get_body_elements(rule, false)?.into();

    // Check for "else" separating truthy and falsey conditions
    let (truthy, falsey) = match elements.iter().position(|x| matches!(x, Element::Partial(PartialElement::Else))) {
        Some(idx) => {
            let truthy = &elements[..idx];
            let falsey = &elements[(idx+1)..];
            // make sure there is no second else. if there is, it's an error
            if falsey.iter().any(|x| matches!(x, Element::Partial(PartialElement::Else))) {
                return Err(parser.make_warn(ParseWarningKind::SecondElse))
            }
            (Vec::from(truthy), Vec::from(falsey))
        }
        _ => {
            (elements, vec![])
        }
    };

    // evaluate right away; 
    match name {
        "if" => {
            if evaluate_if(parser, condition) {
                ok!(true; truthy, vec![])
            } else {
                ok!(true; falsey, vec![])
            }
        }
        "ifexpr" => {
            if evaluate_ifexpr(parser, condition) {
                ok!(true; truthy, vec![])
            } else {
                ok!(true; falsey, vec![])
            }
        }
        _ => unreachable!()
    }
}

fn parse_expr<'r, 't>(
    parser: &mut Parser<'r, 't>,
    name: &'t str,
    flag_star: bool,
    flag_score: bool,
    in_head: bool,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Parsing expression block (name {name}, in-head {in_head})");
    assert!(!flag_star, "Expression doesn't allow star flag");
    assert!(!flag_score, "Expression doesn't allow score flag");

    // syntax: [[#expr expression]]

    let condition = collect_text(
        parser,
        parser.rule(),
        &[],
        &[ParseCondition::current(Token::RightBlock)],
        &[],
        None,
    )?;

    let result = evaluate_expr(parser, condition).to_string();

    ok!(Element::Text(Cow::from(result.to_owned())))
}

fn evaluate_if<'r, 't>(_parser: &mut Parser<'r, 't>, expr: &str) -> bool {
    let expr = expr.trim().to_ascii_lowercase();
    !(expr == "false" || expr == "null" || (expr.starts_with("{$") && expr.ends_with('}')) || (expr.starts_with("%%") && expr.ends_with("%%")))
}

fn evaluate_ifexpr<'r, 't>(parser: &mut Parser<'t, 't>, expr: &str) -> bool {
    match evaluate_expr(parser, expr) {
        ExpressionResult::Bool(b) => b,
        ExpressionResult::Int(i) => i != 0,
        ExpressionResult::Float(f) => f != 0.0,
        ExpressionResult::String(s) => s != "",
        ExpressionResult::None => false
    }
}

fn evaluate_expr<'r, 't>(parser: &mut Parser<'r, 't>, expr: &str) -> ExpressionResult<'static> {
    parser.page_callbacks().evaluate_expression(Cow::from(expr))
}