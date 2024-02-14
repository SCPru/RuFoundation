/*
 * includes/include_ref.rs
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

use crate::data::PageRef;
use crate::tree::VariableMap;

/// Represents an include block.
///
/// It contains the page being included, as well as the arguments
/// to be passed to it when doing the substitution.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq)]
#[serde(rename_all = "kebab-case")]
pub struct IncludeRef<'t> {
    page_ref: PageRef<'t>,
    variables: VariableMap<'t>,
}

impl<'t> IncludeRef<'t> {
    #[inline]
    pub fn new(page_ref: PageRef<'t>, variables: VariableMap<'t>) -> Self {
        IncludeRef {
            page_ref,
            variables,
        }
    }

    #[inline]
    pub fn page_only(page_ref: PageRef<'t>) -> Self {
        IncludeRef::new(page_ref, VariableMap::new())
    }

    #[inline]
    pub fn page_ref(&self) -> &PageRef<'t> {
        &self.page_ref
    }

    #[inline]
    pub fn variables(&self) -> &VariableMap<'t> {
        &self.variables
    }
}

impl<'t> From<IncludeRef<'t>> for (PageRef<'t>, VariableMap<'t>) {
    #[inline]
    fn from(include: IncludeRef<'t>) -> (PageRef<'t>, VariableMap<'t>) {
        let IncludeRef {
            page_ref,
            variables,
        } = include;

        (page_ref, variables)
    }
}