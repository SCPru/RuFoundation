/*
 * parsing/rule/impls/block/blocks/code.rs
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

use super::prelude::*;

pub const BLOCK_CODE: BlockRule = BlockRule {
    name: "block-code",
    accepts_names: &["code"],
    accepts_star: false,
    accepts_score: false,
    accepts_newlines: true,
    accepts_partial: AcceptsPartial::None,
    parse_fn,
};

fn parse_fn<'r, 't>(
    parser: &mut Parser<'r, 't>,
    name: &'t str,
    flag_star: bool,
    flag_score: bool,
    in_head: bool,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Parsing code block (in-head {in_head})");
    assert!(!flag_star, "Code doesn't allow star flag");
    assert!(!flag_score, "Code doesn't allow score flag");
    assert_block_name(&BLOCK_CODE, name);

    let mut arguments = parser.get_head_map(&BLOCK_CODE, in_head)?;
    let language = arguments.get("type");
    
    let code = parser.get_body_text(&BLOCK_CODE, name)?;

    parser.push_code(language.to_owned().unwrap_or(cow!("plain")).as_ref().to_owned(), code.to_owned());

    let element = Element::Code {
        contents: cow!(code),
        language
    };

    ok!(element)
}
