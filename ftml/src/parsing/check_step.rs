/*
 * parsing/check_step.rs
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

use super::{ExtractedToken, ParseWarning, Parser, Token, ParseWarningKind};

/// Helper function to check that the current token matches, then step.
///
/// # Returns
/// The `ExtractedToken` which was checked and stepped over.
///
/// This is similar to parser.get_token(), but it returns the token rather than string.
#[inline]
pub fn check_step<'r, 't>(
    parser: &mut Parser<'r, 't>,
    token: Token,
    kind: ParseWarningKind,
) -> Result<&'r ExtractedToken<'t>, ParseWarning> {
    let current = parser.current();

    if current.token == token {
        parser.step()?;
        Ok(current)
    } else {
        Err(parser.make_warn(kind))
    }
}